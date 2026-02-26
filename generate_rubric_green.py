"""
Generate the updated UGBA 101A Exam 1 Answer Key / Rubric PDF — GREEN (B) version.
Usage: python generate_rubric_green.py
Output: data/rubrics/UGBA101A_Exam1_GREEN_V1.pdf
"""

from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT

OUTPUT = Path(__file__).parent / "data" / "rubrics" / "UGBA101A_Exam1_GREEN_V1.pdf"

# ---------------------------------------------------------------------------
# Styles
# ---------------------------------------------------------------------------
styles = getSampleStyleSheet()

GREEN = colors.HexColor("#007a00")

title_style = ParagraphStyle("title", parent=styles["Title"],
    fontSize=15, spaceAfter=4, alignment=TA_CENTER)
subtitle_style = ParagraphStyle("subtitle", parent=styles["Normal"],
    fontSize=11, spaceAfter=2, alignment=TA_CENTER, textColor=colors.HexColor("#333333"))
sub2_style = ParagraphStyle("sub2", parent=styles["Normal"],
    fontSize=9, spaceAfter=10, alignment=TA_CENTER, textColor=colors.HexColor("#555555"))

h1_style = ParagraphStyle("h1", parent=styles["Heading1"],
    fontSize=12, spaceBefore=14, spaceAfter=4,
    textColor=colors.HexColor("#1a1a2e"), borderPad=2)
h2_style = ParagraphStyle("h2", parent=styles["Heading2"],
    fontSize=11, spaceBefore=10, spaceAfter=3,
    textColor=GREEN)
h3_style = ParagraphStyle("h3", parent=styles["Heading3"],
    fontSize=10, spaceBefore=8, spaceAfter=3,
    textColor=colors.HexColor("#333333"))

body_style = ParagraphStyle("body", parent=styles["Normal"],
    fontSize=9, spaceAfter=3, leading=13)
bold_body = ParagraphStyle("bold_body", parent=body_style,
    fontName="Helvetica-Bold")
note_style = ParagraphStyle("note", parent=body_style,
    textColor=colors.HexColor("#555555"), fontSize=8.5)
answer_style = ParagraphStyle("answer", parent=body_style,
    fontName="Helvetica-Bold", textColor=colors.HexColor("#1a1a2e"))

# ---------------------------------------------------------------------------
# Table helpers
# ---------------------------------------------------------------------------
TBLW = 6.5 * inch
COL_SCENARIO = 4.8 * inch
COL_PTS      = 1.7 * inch

def tier_table(rows, header=True):
    data = [["Scenario", "Points"]] + list(rows) if header else list(rows)
    col_widths = [COL_SCENARIO, COL_PTS]
    t = Table(data, colWidths=col_widths, repeatRows=1 if header else 0)
    style = TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a4d1a")),
        ("TEXTCOLOR",  (0, 0), (-1, 0), colors.white),
        ("FONTNAME",   (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",   (0, 0), (-1, -1), 8.5),
        ("ALIGN",      (1, 0), (1, -1), "CENTER"),
        ("VALIGN",     (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
            [colors.HexColor("#f0fff0"), colors.white]),
        ("GRID",       (0, 0), (-1, -1), 0.4, colors.HexColor("#b2d8b2")),
        ("LEFTPADDING",  (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING",   (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 4),
    ])
    if not header:
        style.add("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f0fff0"))
        style.add("TEXTCOLOR",  (0, 0), (-1, 0), colors.HexColor("#1a1a2e"))
        style.add("FONTNAME",   (0, 0), (-1, 0), "Helvetica")
    t.setStyle(style)
    return t

def section_table(rows):
    t = Table(rows, colWidths=[3.2*inch, 3.3*inch])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a4d1a")),
        ("TEXTCOLOR",  (0, 0), (-1, 0), colors.white),
        ("FONTNAME",   (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME",   (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE",   (0, 0), (-1, -1), 9),
        ("ALIGN",      (1, 0), (1, -1), "CENTER"),
        ("VALIGN",     (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
            [colors.HexColor("#f0fff0"), colors.white]),
        ("GRID",       (0, 0), (-1, -1), 0.4, colors.HexColor("#b2d8b2")),
        ("LEFTPADDING",  (0, 0), (-1, -1), 8),
        ("TOPPADDING",   (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 5),
    ]))
    return t

def mc_table(answers):
    data = [["Question", "Correct Answer"]]
    for q, a in answers:
        data.append([q, a])
    t = Table(data, colWidths=[3.25*inch, 3.25*inch], repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a4d1a")),
        ("TEXTCOLOR",  (0, 0), (-1, 0), colors.white),
        ("FONTNAME",   (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME",   (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE",   (0, 0), (-1, -1), 9),
        ("ALIGN",      (1, 0), (1, -1), "CENTER"),
        ("VALIGN",     (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
            [colors.HexColor("#f0fff0"), colors.white]),
        ("GRID",       (0, 0), (-1, -1), 0.4, colors.HexColor("#b2d8b2")),
        ("LEFTPADDING",  (0, 0), (-1, -1), 8),
        ("TOPPADDING",   (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 4),
    ]))
    return t

def hr():
    return HRFlowable(width="100%", thickness=0.5,
                      color=colors.HexColor("#b2d8b2"), spaceAfter=6)

def sp(n=6):
    return Spacer(1, n)

def p(text, style=None):
    return Paragraph(text, style or body_style)

def h1(text): return Paragraph(text, h1_style)
def h2(text): return Paragraph(text, h2_style)
def h3(text): return Paragraph(text, h3_style)

# ---------------------------------------------------------------------------
# Build document
# ---------------------------------------------------------------------------
def build():
    doc = SimpleDocTemplate(
        str(OUTPUT),
        pagesize=letter,
        leftMargin=0.85*inch, rightMargin=0.85*inch,
        topMargin=0.85*inch,  bottomMargin=0.85*inch,
    )

    story = []

    # ── Title ────────────────────────────────────────────────────────────────
    story += [
        p("UGBA 101A — Microeconomics for Business Decisions", title_style),
        p("Midterm Exam 1 — ANSWER KEY / GRADING RUBRIC — <font color='#007a00'><b>Green (B)</b></font>", subtitle_style),
        p("Chapters 1–6  |  Spring 2026  |  UC Berkeley Haas School of Business  |  V1", sub2_style),
        hr(),
        sp(4),
    ]

    # ── Score summary ────────────────────────────────────────────────────────
    story += [
        h1("Total Points per Section"),
        section_table([
            ["Section", "Questions / Points"],
            ["Part I: Numeric / Calculation (Q1–7)", "30 pts  (5 pts each)"],
            ["Part II: Short Answer (Q8–10)", "10 pts"],
            ["Part III: Multiple Choice (Q11–28)", "60 pts  (3.333334 pts each, capped at 60)"],
            ["TOTAL", "100 pts"],
        ]),
        sp(10),
    ]

    # ── Universal policies ───────────────────────────────────────────────────
    story += [
        h1("Universal Grading Policies"),
        p("<b>No rounding penalties.</b> Do not deduct points for rounding errors in any section."),
        p("<b>Correct answer = full credit.</b> A correct final answer earns full credit regardless "
          "of whether work is shown. Work is only evaluated when the answer is wrong — in that case, "
          "correct method and arithmetic with an incorrect answer may earn partial credit as outlined "
          "per question below."),
        p("<b>Carry-forward credit.</b> If a student's answer to a later part is wrong solely because "
          "of an error made in an earlier part, but their method and arithmetic for the later part are "
          "otherwise correct, award <b>half credit</b> for the later part. Full credit is reserved for "
          "students who arrive at the correct answer. Note in feedback that carry-forward partial credit "
          "was applied."),
        sp(10),
    ]

    # ── PART I: NUMERIC ──────────────────────────────────────────────────────
    story += [
        h1("Part I: Numeric / Short Calculation  (30 points — 5 points each)"),
        sp(4),
    ]

    # Q1 (= Red Q19)
    story += [
        KeepTogether([
            h2("Q1  —  Budget Line  (5 pts)"),
            p("<b>Accepted answers (either form):</b>"),
            p("• Standard form:  5X + 10Y = 200"),
            p("• Slope-intercept form:  Y = −(1/2)X + 20  or  Y = −0.5X + 20"),
            p("<i>Given: Income = $200, P<sub>X</sub> = $5, P<sub>Y</sub> = $10</i>", note_style),
            sp(4),
            tier_table([
                ("Correct answer in either accepted form", "5"),
                ("Correct structure (PxX + PyY = I) but wrong values plugged in", "2"),
                ("Correct slope (−½ or −0.5) but wrong intercept", "2"),
                ("Correct intercepts identifiable from work but equation wrong", "3"),
                ("Correct equation in non-accepted simplified form", "4"),
                ("Correct equation but axes swapped", "4"),
                ("Spending = income concept shown but cannot execute algebraically", "1"),
            ]),
        ]),
        sp(10),
    ]

    # Q2 (= Red Q20)
    story += [
        KeepTogether([
            h2("Q2  —  MRS  (5 pts)"),
            p("<b>Correct answer:</b>  2  (consumer gives up 2 units of clothing per additional unit of food)"),
            p("<i>Method: MRS = |ΔClothing / ΔFood| = |6−10| / |4−2| = 4/2 = 2</i>", note_style),
            sp(4),
            tier_table([
                ("Correct answer: 2", "5"),
                ("Correct answer with wrong sign: −2", "4"),
                ("Inverted ratio — answers ½  (used ΔFood/ΔClothing instead of ΔClothing/ΔFood)", "2.5"),
                ("Correct formula and setup, arithmetic error", "3"),
                ("Answer is order-of-magnitude off (e.g., 20, 0.2, 0.02) but correct work shown", "2.5"),
                ("Identifies correct bundles and columns, wrong execution", "2"),
                ("Wrong bundles used", "1"),
            ]),
        ]),
        sp(10),
    ]

    # Q3 (= Red Q21)
    story += [
        h2("Q3  —  Demand / Consumer Surplus  (5 pts — 2.5 pts per part)"),
        p("<i>Demand equation: P = 50 − 2Q  |  Price = $20</i>", note_style),
        sp(4),
        KeepTogether([
            h3("Q3 Part (a)  —  Quantity Demanded  (2.5 pts)"),
            p("<b>Correct answer:</b>  15,000 tickets  (accept: 15 thousand or 15)"),
            p("<i>Method: 20 = 50 − 2Q → Q = 15</i>", note_style),
            sp(4),
            tier_table([
                ("Correct: 15 / 15,000 / 15 thousand", "2.5"),
                ("Correct substitution shown, arithmetic error", "1.5"),
                ("Sets up equation correctly, does not solve", "1"),
            ]),
        ]),
        sp(8),
        KeepTogether([
            h3("Q3 Part (b)  —  Consumer Surplus  (2.5 pts)"),
            p("<b>Correct answer:</b>  $225,000  (accept: $225 thousand or 225)"),
            p("<i>Method: CS = ½ × (50−20) × 15 = 225 thousand</i>", note_style),
            sp(4),
            tier_table([
                ("Correct: $225,000 / $225 thousand / 225", "2.5"),
                ("Correct CS formula, arithmetic error", "1.5"),
                ("Correct CS formula, wrong Q from part (a) — carry-forward", "1.25"),
                ("Correct CS formula, wrong price used for height", "1"),
                ("Uses rectangle instead of triangle (Q × ΔP), correct numbers", "1"),
            ]),
        ]),
        sp(10),
    ]

    # Q4 (= Red Q22)
    story += [
        h2("Q4  —  Expected Value / Variance / Standard Deviation  (5 pts: 2 / 2 / 1)"),
        p("<i>Payoffs: $500 (p=0.3), $300 (p=0.5), $100 (p=0.2)</i>", note_style),
        sp(4),
        KeepTogether([
            h3("Q4 Part (a)  —  Expected Value  (2 pts)"),
            p("<b>Correct answer:</b>  $320"),
            p("<i>Method: E(X) = 0.3(500) + 0.5(300) + 0.2(100) = 150 + 150 + 20 = 320</i>", note_style),
            sp(4),
            tier_table([
                ("Correct: $320", "2"),
                ("Correct formula, arithmetic error", "1"),
                ("Wrong probabilities, correct weighted sum method", "1"),
            ]),
        ]),
        sp(8),
        KeepTogether([
            h3("Q4 Part (b)  —  Variance  (2 pts)"),
            p("<b>Correct answer:</b>  19,600"),
            p("<i>Method: σ² = 0.3(180)² + 0.5(−20)² + 0.2(−220)² = 9,720 + 200 + 9,680</i>", note_style),
            p("<i>Alternative method E(X²) − μ² is equally valid and earns full credit.</i>", note_style),
            sp(4),
            tier_table([
                ("Correct: 19,600", "2"),
                ("Correct using alternative method E(X²) − μ² — award full credit", "2"),
                ("Correct deviation formula, arithmetic error", "1"),
                ("Wrong mean from part (a), correct method — carry-forward", "1"),
            ]),
        ]),
        sp(8),
        KeepTogether([
            h3("Q4 Part (c)  —  Standard Deviation  (1 pt)"),
            p("<b>Correct answer:</b>  $140"),
            p("<i>Method: σ = √19,600 = 140</i>", note_style),
            sp(4),
            tier_table([
                ("Correct: $140", "1"),
                ("Correct method, arithmetic error", "0.5"),
                ("Correctly takes √ of their own wrong variance — carry-forward", "0.5"),
            ]),
        ]),
        sp(10),
    ]

    # Q5 (= Red Q23)
    story += [
        h2("Q5  —  Risk and Expected Utility  (5 pts: 1.5 / 1.5 / 2)"),
        p("<i>Income: $10,000 (p=0.5) or $30,000 (p=0.5)  |  U($10,000)=10, U($20,000)=16, U($30,000)=18, U($12,000)=14</i>", note_style),
        sp(4),
        KeepTogether([
            h3("Q5 Part (a)  —  Expected Income  (1.5 pts)"),
            p("<b>Correct answer:</b>  $20,000"),
            p("<i>Method: E(I) = 0.5(10,000) + 0.5(30,000) = 20,000</i>", note_style),
            sp(4),
            tier_table([
                ("Correct: $20,000", "1.5"),
                ("Correct weighted sum method, arithmetic error", "0.75"),
                ("Wrong probabilities, correct method", "0.75"),
            ]),
        ]),
        sp(8),
        KeepTogether([
            h3("Q5 Part (b)  —  Expected Utility  (1.5 pts)"),
            p("<b>Correct answer:</b>  14"),
            p("<i>Method: E(U) = 0.5(10) + 0.5(18) = 5 + 9 = 14</i>", note_style),
            sp(4),
            tier_table([
                ("Correct: 14", "1.5"),
                ("Correct method, arithmetic error", "0.75"),
                ("Applies utility function correctly to wrong E(I) from part (a) — carry-forward", "0.75"),
                ("Wrong utility values used, correct weighted method", "0.75"),
            ]),
        ]),
        sp(8),
        KeepTogether([
            h3("Q5 Part (c)  —  Risk Premium  (2 pts)"),
            p("<b>Correct answer:</b>  $8,000"),
            p("<i>Method: CE = $12,000 (yields U=14)  |  RP = E(I) − CE = 20,000 − 12,000 = 8,000</i>", note_style),
            sp(4),
            tier_table([
                ("Correct: $8,000", "2"),
                ("Correct answer with wrong sign: −$8,000", "1"),
                ("Correctly identifies CE = $12,000 and uses RP = E(I) − CE, arithmetic error", "1.5"),
                ("Correct formula RP = E(I) − CE, wrong CE due to wrong E(U) — carry-forward", "1"),
                ("States RP = E(I) − CE but cannot identify CE", "0.5"),
                ("Confuses risk premium with variance or standard deviation", "0"),
            ]),
        ]),
        sp(10),
    ]

    # Q6 (= Red Q24)
    story += [
        h2("Q6  —  Real Price of Butter  (5 pts — 2.5 pts per part)"),
        p("<i>CPI<sub>1980</sub> = 82.4  |  CPI<sub>2000</sub> = 172.2  |  Nominal price 1980 = $1.88  |  Nominal price 2000 = $2.52</i>", note_style),
        sp(4),
        KeepTogether([
            h3("Q6 Part (a)  —  Real Price in 2000  (2.5 pts)"),
            p("<b>Correct answer:</b>  $1.21  (accept any answer in range $1.20–$1.22)"),
            p("<i>Method: (CPI<sub>1980</sub> / CPI<sub>2000</sub>) × Nominal Price<sub>2000</sub> = (82.4 / 172.2) × $2.52 ≈ $1.21</i>", note_style),
            sp(4),
            tier_table([
                ("Correct: $1.20–$1.22", "2.5"),
                ("Correct formula structure, arithmetic error outside accepted range", "1.5"),
                ("Inverts CPI ratio (172.2/82.4) but otherwise correct setup", "1"),
                ("Sets up formula with wrong nominal price, correct CPI ratio", "1"),
            ]),
        ]),
        sp(8),
        KeepTogether([
            h3("Q6 Part (b)  —  Direction of Change  (2.5 pts)"),
            p("<b>Correct answer:</b>  Decreased"),
            sp(4),
            tier_table([
                ("Correct: 'Decreased'", "2.5"),
                ("Wrong direction but consistent with their wrong part (a) — carry-forward", "1.25"),
                ("No answer or unsupported guess", "0"),
            ]),
        ]),
        sp(10),
    ]

    # Q7 (= Red Q25)
    story += [
        h2("Q7  —  International Trade  (5 pts — 2.5 pts per part)"),
        p("<i>Demand: Q = 40 − 2P  |  Supply: Q = (2/3)P  |  World price = $9</i>", note_style),
        sp(4),
        KeepTogether([
            h3("Q7 Part (a)  —  U.S. Quantity Demanded at World Price  (2.5 pts)"),
            p("<b>Correct answer:</b>  22 million pounds  (accept 21.95–22.05)"),
            p("<i>Method: Q = 40 − 2(9) = 22</i>", note_style),
            sp(4),
            tier_table([
                ("Correct: 22 / 21.95–22.05 million pounds", "2.5"),
                ("Correct substitution into demand equation, arithmetic error", "1.5"),
                ("Uses wrong equation (supply instead of demand), correct substitution", "1"),
            ]),
        ]),
        sp(8),
        KeepTogether([
            h3("Q7 Part (b)  —  U.S. Domestic Supply at World Price  (2.5 pts)"),
            p("<b>Correct answer:</b>  6 million pounds  (accept 5.95–6.05)"),
            p("<i>Method: Q = (2/3)(9) = 6</i>", note_style),
            sp(4),
            tier_table([
                ("Correct: 6 / 5.95–6.05 million pounds", "2.5"),
                ("Correct substitution into supply equation, arithmetic error", "1.5"),
                ("Uses wrong equation (demand instead of supply), correct substitution", "1"),
            ]),
        ]),
        sp(10),
    ]

    # ── PART II: SHORT ANSWER ────────────────────────────────────────────────
    story += [
        h1("Part II: Short Answer  (10 points)"),
        sp(4),
    ]

    # Q8 (= Red Q26)
    story += [
        h2("Q8  —  Behavioral Economics and Consumer Demand"),
        sp(4),
        KeepTogether([
            h3("Q8 Part (a)  —  Fairness Bias and Demand  (2 pts)"),
            p("Student must identify <b>both</b> of the following effects:"),
            p("1. The demand curve shifts <b>outward (rightward)</b> due to the blizzard, increasing demand."),
            p("2. Beyond a price perceived as unfair, demand <b>bends back / shifts sharply leftward</b> — "
              "higher prices generate far fewer purchases than standard demand theory predicts."),
            sp(4),
            tier_table([
                ("Identifies both effects clearly", "2"),
                ("Identifies only the fairness/backward bend effect", "1"),
                ("Identifies only the outward blizzard shift", "0.5"),
                ("Mentions price gouging or fairness vaguely without explaining demand curve effects", "0.5"),
            ]),
        ]),
        sp(8),
        KeepTogether([
            h3("Q8 Part (b)  —  Figure 1 and Figure 2: Movement A to B  (2 pts — 1 pt each)"),
            p("<b>Figure 1:</b> Movement from A to B is caused by a decrease in price ($2.00 → $1.00) — "
              "a <b>movement along</b> the existing demand curve D<sub>1</sub>. This is a change in quantity demanded, "
              "not a shift in demand."),
            p("<b>Figure 2:</b> Movement from A to B is caused by an increase in demand — a <b>rightward "
              "shift</b> of the entire demand curve from D<sub>1</sub> to D<sub>2</sub> — resulting from a non-price factor "
              "(e.g., increase in income for a normal good, rise in price of a substitute, fall in price "
              "of a complement, or favorable change in preferences)."),
            sp(4),
            tier_table([
                ("Fig 1: Correctly identifies movement along curve due to price decrease", "1"),
                ("Fig 1: Correct conclusion but uses 'shift' instead of movement along curve", "0"),
                ("Fig 2: Correctly identifies rightward shift from any valid non-price factor", "1"),
                ("Fig 2: Names a valid non-price shifter but calls it a movement along the curve", "0.5"),
            ]),
        ]),
        sp(10),
    ]

    # Q9 (= Red Q27)
    story += [
        KeepTogether([
            h2("Q9  —  Fill in the Table  (4 pts)"),
            p("Award points by row. Within each row, both computed cells must be correct for full row credit; "
              "one of two correct earns half row credit; both wrong earns 0."),
            sp(4),
            tier_table([
                ("L=2: TP and MP both correct  (AP=300 given → TP=600, MP=375)", "1.5"),
                ("L=2: One of two cells correct", "0.75"),
                ("L=3: TP and AP both correct  (MP=300 given → TP=900, AP=300)", "1.5"),
                ("L=3: One of two cells correct", "0.75"),
                ("L=4: MP and AP both correct  (TP=1,140 given → MP=240, AP=285)", "1"),
                ("L=4: One of two cells correct", "0.5"),
            ]),
            sp(6),
            p("<b>Complete answer key:</b>", bold_body),
        ]),
        Table(
            [
                ["L", "Total Output (TP)", "Marginal Product (MP)", "Average Product (AP)"],
                ["0", "0", "—", "—"],
                ["1", "225", "225", "225"],
                ["2", "600", "375", "300  ← given"],
                ["3", "900", "300  ← given", "300"],
                ["4", "1,140  ← given", "240", "285"],
            ],
            colWidths=[0.6*inch, 1.6*inch, 1.8*inch, 1.9*inch],
            style=TableStyle([
                ("BACKGROUND", (0,0),(-1,0), colors.HexColor("#1a4d1a")),
                ("TEXTCOLOR",  (0,0),(-1,0), colors.white),
                ("FONTNAME",   (0,0),(-1,0), "Helvetica-Bold"),
                ("FONTNAME",   (0,1),(-1,-1), "Helvetica"),
                ("FONTSIZE",   (0,0),(-1,-1), 8.5),
                ("ALIGN",      (0,0),(-1,-1), "CENTER"),
                ("VALIGN",     (0,0),(-1,-1), "MIDDLE"),
                ("ROWBACKGROUNDS",(0,1),(-1,-1),
                    [colors.HexColor("#f0fff0"), colors.white]),
                ("GRID",       (0,0),(-1,-1), 0.4, colors.HexColor("#b2d8b2")),
                ("TOPPADDING",    (0,0),(-1,-1), 4),
                ("BOTTOMPADDING", (0,0),(-1,-1), 4),
            ]),
        ),
        sp(10),
    ]

    # Q10 (= Red Q28)
    story += [
        KeepTogether([
            h2("Q10  —  Returns to Scale: q = L² + L  (2 pts)"),
            p("<b>Correct answer:</b>  Increasing Returns to Scale (IRS)"),
            p("<i>Method: Scale input by t &gt; 1:  q(tL) = t²L² + tL  vs.  t·q(L) = tL² + tL. "
              "Since t²L² &gt; tL² for t &gt; 1, L &gt; 0, we have q(tL) &gt; t·q(L) → IRS.</i>", note_style),
            p("<i>Note: The function is not homogeneous of a single degree (L² and L terms scale "
              "differently), but the L² term always dominates for t &gt; 1 and L &gt; 0, yielding "
              "IRS throughout.</i>", note_style),
            sp(4),
            tier_table([
                ("Correct: IRS with any valid justification or scaling logic", "2"),
                ("Correct: IRS with no justification", "0.5"),
                ("Uses numerical example (e.g., t=2, L=1) and correctly concludes IRS", "1"),
                ("Incorrect answer but demonstrates valid scaling attempt with algebra", "0.5"),
                ("Correct algebraic setup, wrong conclusion (e.g., concludes CRS)", "0.5"),
                ("Incorrect answer with no work", "0"),
            ]),
        ]),
        sp(10),
    ]

    # ── PART III: MULTIPLE CHOICE ─────────────────────────────────────────────
    story += [
        h1("Part III: Multiple Choice  (60 points — 3.333334 points each)"),
        p("Identify which single letter (A, B, C, or D) the student has circled or marked. "
          "Award 3.333334 points if it matches the correct answer below. Award 0 points otherwise. "
          "Do not award partial credit."),
        sp(4),
        p("<b>Ambiguous or changed answers:</b>"),
        p("• If a student has crossed out one answer and clearly marked another, score the remaining mark."),
        p("• If two answers appear marked with no clear cancellation, award 0."),
        p("• If a student writes a letter in the margin or nearby, defer to whatever is circled on the "
          "answer choices. If nothing is circled, score the written letter."),
        p("• If the mark is physically ambiguous (partial circle, stray mark), award 0 and note it in feedback."),
        p("<b>Scoring note:</b> Score each correct answer as 3.333334 points. Report the raw MC sum "
          "rounded to two decimal places, with a maximum of 60.00."),
        sp(8),
        mc_table([
            ("Q11","C"),("Q12","B"),("Q13","A"),("Q14","B"),("Q15","B"),
            ("Q16","C"),("Q17","C"),("Q18","B"),("Q19","B"),("Q20","B"),
            ("Q21","B"),("Q22","B"),("Q23","A"),("Q24","A"),("Q25","B"),
            ("Q26","B"),("Q27","D"),("Q28","B"),
        ]),
        sp(14),
        hr(),
        p("— END OF ANSWER KEY / GRADING RUBRIC —", subtitle_style),
    ]

    doc.build(story)
    print(f"Generated: {OUTPUT}")

if __name__ == "__main__":
    build()
