"""
Audit Grader — Independent re-grading for inter-rater reliability testing.
===========================================================================
Re-grades a sample of already-graded exams using Opus 4.6, then compares
against the production Sonnet 4.6 grades. Outputs comparison JSON for the
/testing agent to analyze.

Usage:
    python audit_grader.py                         # default: 10 random graded exams
    python audit_grader.py --sample-size 5         # 5 exams
    python audit_grader.py --version RED           # only RED version exams
    python audit_grader.py --batch 1               # only batch 1
    python audit_grader.py --anon-ids X1,X2,X3     # specific exams

PRIVACY: identical to production — only anon_id + answer pages + rubric
are sent to the API. No student names, no cover pages.
"""

import argparse
import base64
import io
import json
import logging
import os
import re
import secrets
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

import anthropic
import httpx
import pypdfium2 as pdfium
from PIL import Image, ImageEnhance

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "exam_grader.db"
AUDIT_DIR = DATA_DIR / "audit_results"

# Audit model — Opus 4.6 for independent verification
AUDIT_MODEL = "claude-opus-4-6"

# Production model — for labeling in output
PRODUCTION_MODEL = "claude-sonnet-4-6"

MAX_SAMPLE = 10  # hard cap per run

_client = anthropic.Anthropic(
    api_key=os.environ.get("ANTHROPIC_API_KEY"),
    timeout=httpx.Timeout(600.0, connect=10.0),
)

# Logger — shared with production grading log
_log = logging.getLogger("rubrica")
_log.setLevel(logging.INFO)
if not _log.handlers:
    _handler = logging.FileHandler(DATA_DIR / "grading.log", encoding="utf-8")
    _handler.setFormatter(logging.Formatter("%(asctime)s  %(levelname)-7s  %(message)s"))
    _log.addHandler(_handler)

# Console output for interactive use
_console = logging.StreamHandler()
_console.setFormatter(logging.Formatter("%(message)s"))
_log.addHandler(_console)

# PDF rendering lock (pypdfium2 is not thread-safe)
_pdfium_lock = threading.Lock()


# ---------------------------------------------------------------------------
# Pipeline functions — replicated from grader.py to hold all variables
# constant except the model.
# ---------------------------------------------------------------------------

def _render_page_png(pdf_path: str, page_num: int, scale: float = 2.0) -> bytes:
    """Render a single PDF page to PNG bytes."""
    with _pdfium_lock:
        doc = pdfium.PdfDocument(pdf_path)
        try:
            page = doc[page_num]
            bitmap = page.render(scale=scale)
            pil_img = bitmap.to_pil()
            buf = io.BytesIO()
            pil_img.save(buf, format="PNG")
            result = buf.getvalue()
            del pil_img, bitmap, page
            return result
        finally:
            doc.close()


def letter_grade(pct: float) -> str:
    if pct >= 90: return "A"
    if pct >= 80: return "B"
    if pct >= 70: return "C"
    if pct >= 60: return "D"
    return "F"


# Deliberation language pattern — identical to production
_DELIBERATION = re.compile(
    r'\b(wait|actually|hmm|let me re-?(?:read|check|count|examine)|'
    r'on second thought|re-?reading|I (?:think|miscounted|need to)|'
    r'looking (?:again|more carefully)|hold on|scratch that|'
    r'no,|correction:|upon (?:closer|further))\b',
    re.IGNORECASE,
)


def _clean_feedback(text: str) -> str:
    """Strip deliberation language and normalize dashes."""
    if not text:
        return text
    text = text.replace("\u2014", "-").replace("\u2013", "-")
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    clean = [s for s in sentences if not _DELIBERATION.search(s)]
    result = " ".join(clean).strip()
    return result if result else sentences[-1].strip()


def audit_grade_exam(exam_row, rubric) -> dict:
    """Grade an exam using Opus 4.6 — identical pipeline to production except model.

    Replicates: page rendering, contrast enhancement, system prompt, JSON parsing,
    sub-part consolidation, feedback sanitizer, score recalculation, normalization.
    Does NOT run: feedback specificity enforcement or boundary re-grade (those are
    production-only features; the audit measures raw model output).
    """
    doc = pdfium.PdfDocument(exam_row["file_path"])
    total = len(doc)
    doc.close()
    if total < 2:
        raise ValueError("Exam PDF must have at least 2 pages (cover + answers).")

    # --- Rubric block ---
    rubric_file = rubric["rubric_file_path"] if rubric["rubric_file_path"] else None
    rubric_blocks = []
    if rubric_file and Path(rubric_file).exists() and rubric_file.lower().endswith(".pdf"):
        with open(rubric_file, "rb") as f:
            rubric_b64 = base64.standard_b64encode(f.read()).decode()
        rubric_blocks = [
            {"type": "text", "text": "RUBRIC (read the document below carefully before grading):"},
            {
                "type": "document",
                "source": {"type": "base64", "media_type": "application/pdf", "data": rubric_b64},
            },
        ]
    else:
        rubric_blocks = [
            {"type": "text", "text": f"RUBRIC:\n{rubric['content']}"},
        ]

    # --- Exam answer page images (skip page 0) ---
    exam_blocks = []
    for page_num in range(1, total):
        img_bytes = _render_page_png(exam_row["file_path"], page_num)
        img = Image.open(io.BytesIO(img_bytes))
        img = ImageEnhance.Contrast(img).enhance(2.0)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        img_bytes = buf.getvalue()
        b64 = base64.standard_b64encode(img_bytes).decode()
        exam_blocks.append({
            "type": "image",
            "source": {"type": "base64", "media_type": "image/png", "data": b64},
        })
        exam_blocks.append({"type": "text", "text": f"[Page {page_num + 1}]"})

    content = rubric_blocks + [
        {"type": "text", "text": "--- EXAM ANSWER PAGES ---"},
        *exam_blocks,
        {
            "type": "text",
            "text": (
                f"Please grade this exam.\n\n"
                f"EXAM ID: {exam_row['anon_id']}\n"
                f"VERSION: {exam_row['version']}\n\n"
                f"Grade each question strictly according to the rubric above. "
                f"Respond ONLY with the JSON object specified in the system prompt."
            ),
        },
    ]

    # System prompt — identical to production
    system_prompt = f"""You are an impartial exam grader. You will grade handwritten exams anonymously by reading the page images provided.

EXAM VERSION: {exam_row["version"]}
ANONYMOUS EXAM ID: {exam_row["anon_id"]}

Grading instructions:
- The rubric is provided at the start of the user message.
- Read the handwritten answers directly from the exam page images.
- Grade each question strictly according to the rubric.
- Some answers may be written in faint pencil — examine the image carefully before concluding a question is blank or unanswered.
- Be fair and consistent. Do not infer the student's identity.

MULTIPLE CHOICE instructions (critical):
- Each MC question lists options VERTICALLY in order: A (top), B (second), C (third), D (bottom).
- The student circles exactly one letter. That circled letter is their answer.
- READ THE ACTUAL LETTER INSIDE OR NEXT TO THE CIRCLE — do not infer the answer from position alone.
- B and D look similar when handwritten. Look carefully: B has two bumps on the right; D has one large curve.
- If a circle is around the second option, confirm it says "B" not "D" before recording.
- The circled letter IS the student's answer — compare it directly to the correct answer in the rubric table.
- Award full points if the circled letter matches the correct answer. Award 0 otherwise.
- Do NOT award partial credit on multiple choice.
- If no letter is clearly marked, award 0 and note "no answer marked" in feedback.
- If two letters appear marked, use the one with the clearest, most deliberate marking.

QUESTION CONSOLIDATION (critical):
- Each question must appear as a SINGLE entry in the scores array, even if the rubric breaks it into sub-parts (a), (b), (c).
- Sum all sub-part points into one earned_points and one max_points for the parent question.
- Use the question number only (e.g. "Q3", "Q22") — never "Q3a", "Q3b", "Q22a", etc.
- Include feedback for all sub-parts combined in the single feedback string.

FEEDBACK TONE (critical):
- Write feedback as a professor would on a graded exam — definitive, concise, and authoritative.
- State what is correct or incorrect directly. Never hedge, self-correct, or show reasoning process.
- NEVER use phrases like "wait", "actually", "let me reconsider", "on second thought", "hmm", or similar deliberation language.
- If you are uncertain about a reading, make your best judgment and commit to it. Do not narrate your uncertainty.
- Good: "Correct application of the Coase theorem."
- Good: "Incorrect — confused fixed and variable costs in the calculation."
- Bad: "Wait, actually I think the student might have meant... let me look again..."

- Respond ONLY with valid JSON in exactly this format:
{{
  "anon_id": "{exam_row["anon_id"]}",
  "scores": [
    {{"question": "Q1", "max_points": <n>, "earned_points": <n>, "feedback": "<specific feedback>"}}
  ],
  "total_earned": <n>,
  "total_possible": <n>,
  "letter_grade": "<A/B/C/D/F>",
  "overall_feedback": "<2-3 sentence summary>"
}}"""

    # --- API call with retry (identical to production) ---
    MAX_ATTEMPTS = 2
    last_error = None
    data = None

    for attempt in range(1, MAX_ATTEMPTS + 1):
        with _client.messages.stream(
            model=AUDIT_MODEL,
            max_tokens=8192,
            temperature=0.0,
            system=system_prompt,
            messages=[{"role": "user", "content": content}],
        ) as stream:
            full_response = stream.get_final_message()

        if full_response.stop_reason == "max_tokens":
            raise ValueError("Response was cut off (max_tokens reached).")

        response_text = ""
        for block in full_response.content:
            if block.type == "text":
                response_text = block.text
                break

        start = response_text.find("{")
        if start == -1:
            last_error = ValueError(f"No JSON found: {response_text[:500]}")
            _log.warning("[AUDIT] Attempt %d/%d for %s: no JSON", attempt, MAX_ATTEMPTS, exam_row["anon_id"])
            continue

        # Find the matching closing brace by tracking nesting depth.
        # Opus sometimes appends commentary or a second JSON object after
        # the main response — rfind("}") would grab too much.
        depth = 0
        end = -1
        in_string = False
        escape = False
        for i in range(start, len(response_text)):
            ch = response_text[i]
            if escape:
                escape = False
                continue
            if ch == '\\' and in_string:
                escape = True
                continue
            if ch == '"' and not escape:
                in_string = not in_string
                continue
            if in_string:
                continue
            if ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break

        if end == -1:
            last_error = ValueError(f"Unbalanced JSON braces: {response_text[:500]}")
            _log.warning("[AUDIT] Attempt %d/%d for %s: unbalanced JSON", attempt, MAX_ATTEMPTS, exam_row["anon_id"])
            continue

        try:
            data = json.loads(response_text[start:end])
            break
        except json.JSONDecodeError as e:
            last_error = e
            _log.warning("[AUDIT] Attempt %d/%d for %s: malformed JSON - %s", attempt, MAX_ATTEMPTS, exam_row["anon_id"], e)
            continue

    if data is None:
        raise last_error or ValueError("Audit grading failed after retries")

    # --- Post-processing (identical to production) ---

    # Sub-part consolidation
    if data.get("scores"):
        merged = {}
        order = []
        for s in data["scores"]:
            raw = str(s.get("question", "")).strip()
            parent = re.sub(r'[\s\-_\.]?\(?[a-zA-Z]\)?$', '', raw).strip()
            if not parent:
                parent = raw
            if parent not in merged:
                merged[parent] = {"max_points": 0, "earned_points": 0, "feedbacks": []}
                order.append(parent)
            merged[parent]["max_points"] += float(s.get("max_points", 0))
            merged[parent]["earned_points"] += float(s.get("earned_points", 0))
            fb = s.get("feedback", "").strip()
            if fb:
                label = raw if raw != parent else ""
                merged[parent]["feedbacks"].append(f"{label}: {fb}" if label else fb)
        data["scores"] = [
            {
                "question": k,
                "max_points": round(v["max_points"], 2),
                "earned_points": round(v["earned_points"], 2),
                "feedback": " | ".join(v["feedbacks"]),
            }
            for k, v in [(k, merged[k]) for k in order]
        ]

    # Feedback sanitizer
    if data.get("scores"):
        for s in data["scores"]:
            if s.get("feedback"):
                s["feedback"] = _clean_feedback(s["feedback"])
    if data.get("overall_feedback"):
        data["overall_feedback"] = _clean_feedback(data["overall_feedback"])

    # Score recalculation
    if data.get("scores"):
        sum_possible = sum(float(s.get("max_points", 0)) for s in data["scores"])
        sum_earned = sum(float(s.get("earned_points", 0)) for s in data["scores"])
        missed = sum_possible - sum_earned
        reported_possible = float(data.get("total_possible", sum_possible))
        data["total_earned"] = round(max(reported_possible - missed, 0), 2)

    # Total normalization
    raw_possible = data.get("total_possible", 0)
    intended = round(raw_possible)
    if intended > 0 and abs(raw_possible - intended) < 0.5:
        scale = intended / raw_possible
        data["total_earned"] = round(data.get("total_earned", 0) * scale, 2)
        data["total_possible"] = intended

    # Letter grade recalculation
    if data.get("total_possible", 0) > 0:
        pct = data["total_earned"] / data["total_possible"] * 100
        data["letter_grade"] = letter_grade(pct)

    # Hard cap
    if data.get("total_possible", 0) > 0:
        data["total_earned"] = min(data["total_earned"], data["total_possible"])

    return data


# ---------------------------------------------------------------------------
# Sampling
# ---------------------------------------------------------------------------

def select_sample(conn, sample_size: int, version: str = None,
                  batch: int = None, anon_ids: list = None) -> list:
    """Select a stratified random sample of graded exams."""
    if anon_ids:
        placeholders = ",".join("?" for _ in anon_ids)
        rows = conn.execute(
            f"SELECT * FROM exams WHERE anon_id IN ({placeholders}) AND grade_data IS NOT NULL",
            anon_ids,
        ).fetchall()
        return rows

    query = "SELECT * FROM exams WHERE grade_data IS NOT NULL"
    params = []
    if version:
        query += " AND version=?"
        params.append(version)
    if batch is not None:
        query += " AND batch=?"
        params.append(batch)

    rows = conn.execute(query, params).fetchall()
    if not rows:
        return []

    # Exclude previously audited exams if audit history exists
    audited = set()
    if AUDIT_DIR.exists():
        for f in AUDIT_DIR.glob("audit_*.json"):
            try:
                with open(f) as fh:
                    prev = json.load(fh)
                for item in prev.get("comparisons", []):
                    audited.add(item.get("anon_id"))
            except (json.JSONDecodeError, KeyError):
                continue

    candidates = [r for r in rows if r["anon_id"] not in audited]
    if not candidates:
        _log.info("[AUDIT] All graded exams already audited. Sampling from full pool.")
        candidates = list(rows)

    # Secure random sampling
    if len(candidates) <= sample_size:
        return candidates

    # Use secrets for cryptographic randomness (parity with anon_id generation)
    indices = list(range(len(candidates)))
    selected = []
    for _ in range(sample_size):
        idx = secrets.randbelow(len(indices))
        selected.append(candidates[indices.pop(idx)])
    return selected


# ---------------------------------------------------------------------------
# Comparison
# ---------------------------------------------------------------------------

def compare_grades(original: dict, audit: dict) -> dict:
    """Compare original and audit grade_data, produce per-question diffs."""
    orig_scores = {s["question"]: s for s in original.get("scores", [])}
    audit_scores = {s["question"]: s for s in audit.get("scores", [])}
    all_questions = sorted(set(orig_scores.keys()) | set(audit_scores.keys()))

    per_question = []
    for q in all_questions:
        orig_s = orig_scores.get(q, {})
        audit_s = audit_scores.get(q, {})
        orig_earned = float(orig_s.get("earned_points", 0))
        audit_earned = float(audit_s.get("earned_points", 0))
        max_pts = float(orig_s.get("max_points", 0) or audit_s.get("max_points", 0))
        diff = orig_earned - audit_earned

        per_question.append({
            "question": q,
            "max_points": max_pts,
            "original_earned": orig_earned,
            "audit_earned": audit_earned,
            "diff": round(diff, 2),
            "abs_diff": round(abs(diff), 2),
            "exact_match": orig_earned == audit_earned,
            "within_1": abs(diff) <= 1.0,
            "original_feedback": orig_s.get("feedback", ""),
            "audit_feedback": audit_s.get("feedback", ""),
        })

    orig_pct = original["total_earned"] / original["total_possible"] * 100 if original.get("total_possible") else 0
    audit_pct = audit["total_earned"] / audit["total_possible"] * 100 if audit.get("total_possible") else 0

    return {
        "original_total": original.get("total_earned", 0),
        "audit_total": audit.get("total_earned", 0),
        "original_pct": round(orig_pct, 1),
        "audit_pct": round(audit_pct, 1),
        "original_grade": original.get("letter_grade", "?"),
        "audit_grade": audit.get("letter_grade", "?"),
        "grade_match": original.get("letter_grade") == audit.get("letter_grade"),
        "total_diff": round(original.get("total_earned", 0) - audit.get("total_earned", 0), 2),
        "per_question": per_question,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Audit grader — independent re-grading for reliability testing")
    parser.add_argument("--sample-size", type=int, default=10, help="Number of exams to audit (max 10)")
    parser.add_argument("--version", type=str, default=None, help="Filter by exam version (e.g. RED)")
    parser.add_argument("--batch", type=int, default=None, help="Filter by batch number")
    parser.add_argument("--anon-ids", type=str, default=None, help="Comma-separated specific anon_ids to audit")
    args = parser.parse_args()

    sample_size = min(args.sample_size, MAX_SAMPLE)
    anon_ids = [a.strip() for a in args.anon_ids.split(",")] if args.anon_ids else None

    AUDIT_DIR.mkdir(exist_ok=True)

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row

    # Select sample
    sample = select_sample(conn, sample_size, args.version, args.batch, anon_ids)
    if not sample:
        _log.info("[AUDIT] No graded exams found matching criteria.")
        conn.close()
        return

    _log.info("[AUDIT] Starting audit of %d exams using %s", len(sample), AUDIT_MODEL)

    comparisons = []
    for exam in sample:
        anon_id = exam["anon_id"]
        original = json.loads(exam["grade_data"])

        rubric = conn.execute(
            "SELECT * FROM rubrics WHERE version=? ORDER BY id DESC LIMIT 1",
            (exam["version"],)
        ).fetchone()
        if not rubric:
            _log.error("[AUDIT] No rubric for %s version %s, skipping", anon_id, exam["version"])
            continue

        _log.info("[AUDIT] Grading %s (%s, batch %s)...", anon_id, exam["version"], exam["batch"])

        try:
            audit_data = audit_grade_exam(exam, rubric)
            comparison = compare_grades(original, audit_data)
            comparison["anon_id"] = anon_id
            comparison["version"] = exam["version"]
            comparison["batch"] = exam["batch"]
            comparisons.append(comparison)

            _log.info("[AUDIT] %s: original %.1f/%d (%s) vs audit %.1f/%d (%s) | diff %+.1f",
                      anon_id,
                      original.get("total_earned", 0), original.get("total_possible", 0),
                      original.get("letter_grade", "?"),
                      audit_data.get("total_earned", 0), audit_data.get("total_possible", 0),
                      audit_data.get("letter_grade", "?"),
                      comparison["total_diff"])
        except Exception as e:
            _log.error("[AUDIT] Failed to grade %s: %s", anon_id, e)
            continue

    conn.close()

    if not comparisons:
        _log.info("[AUDIT] No successful audits completed.")
        return

    # --- Write results ---
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    output = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "audit_model": AUDIT_MODEL,
        "production_model": PRODUCTION_MODEL,
        "sample_size": len(comparisons),
        "comparisons": comparisons,
    }

    output_path = AUDIT_DIR / f"audit_{timestamp}.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    _log.info("[AUDIT] Results written to %s", output_path)

    # --- Print summary ---
    exact_matches = sum(1 for c in comparisons if c["grade_match"])
    total_diffs = [c["total_diff"] for c in comparisons]
    avg_diff = sum(total_diffs) / len(total_diffs)

    all_q_exact = sum(q["exact_match"] for c in comparisons for q in c["per_question"])
    all_q_within1 = sum(q["within_1"] for c in comparisons for q in c["per_question"])
    all_q_total = sum(len(c["per_question"]) for c in comparisons)
    all_q_abs_diffs = [q["abs_diff"] for c in comparisons for q in c["per_question"]]
    mae = sum(all_q_abs_diffs) / len(all_q_abs_diffs) if all_q_abs_diffs else 0

    print("\n" + "=" * 60)
    print(f"AUDIT SUMMARY — {len(comparisons)} exams")
    print(f"Auditor: {AUDIT_MODEL} | Production: {PRODUCTION_MODEL}")
    print("=" * 60)
    print(f"Letter Grade Agreement:  {exact_matches}/{len(comparisons)} ({exact_matches/len(comparisons)*100:.0f}%)")
    print(f"Exact Score Match:       {all_q_exact}/{all_q_total} ({all_q_exact/all_q_total*100:.0f}%)" if all_q_total else "")
    print(f"Within-1-Point:          {all_q_within1}/{all_q_total} ({all_q_within1/all_q_total*100:.0f}%)" if all_q_total else "")
    print(f"Mean Absolute Error:     {mae:.2f} pts")
    print(f"Mean Bias (orig-audit):  {avg_diff:+.2f} pts")
    print(f"\nResults: {output_path}")
    print("=" * 60)

    # Flag disagreements
    for c in comparisons:
        if not c["grade_match"]:
            print(f"  !! {c['anon_id']}: {c['original_grade']} ({c['original_pct']}%) vs "
                  f"{c['audit_grade']} ({c['audit_pct']}%)")


if __name__ == "__main__":
    main()
