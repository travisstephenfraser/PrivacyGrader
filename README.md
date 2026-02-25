# Exam Anonymizer & Grader

A privacy-first Flask web app that anonymizes student exams, grades them using Claude's vision AI against a user-defined rubric, and maps results back to student names — all locally. Student names are never sent to Claude.

Built while serving as a Graduate Student Instructor for Microeconomics at UC Berkeley Haas.

---

## How It Works

1. **Upload a class roster** — student names and SIDs are stored locally in a SQLite database
2. **Upload exams** — individual PDFs or a batch PDF that the app splits automatically
3. **Assign anonymous IDs** — each exam is mapped to a random 8-character ID; names stay local
4. **Upload a rubric** — PDF or DOCX format; the rubric is what gets sent to Claude along with the anonymized exam
5. **Grade** — Claude's vision AI reads each exam image and scores it against the rubric
6. **Review & export** — grades are mapped back to student names locally and can be exported to CSV

Student names and roster data never leave your machine at any point in this process.

---

## Features

- Batch PDF splitting — upload one file for the whole class, the app handles the rest
- Anonymous grading — random IDs replace student names before any API call
- Fuzzy roster matching — local OCR name/SID matching with common character confusion corrections (O→0, l→1, etc.)
- Progress tracking — live grading progress view with per-exam status
- Analytics dashboard — class score distribution, letter grade breakdown
- Rubric versioning — upload and manage multiple rubric versions
- Student reports — individual report view per student
- Export to CSV — final grades with names re-attached locally
- Docs page — built-in documentation at `/docs`

---

## Tech Stack

| Layer | Technology |
|---|---|
| Web framework | Flask 3.x |
| AI grading | Anthropic Claude (vision) |
| PDF handling | pdfplumber, pypdf, pypdfium2 |
| Document parsing | python-docx |
| Database | SQLite (local) |
| Frontend | Bootstrap 5 |

---

## Setup

**Requirements:** Python 3.10+, an [Anthropic API key](https://console.anthropic.com/)

```bash
git clone https://github.com/your-username/exam-grader.git
cd exam-grader
pip install -r requirements.txt
```

Set your API key as an environment variable:

```bash
# Mac/Linux
export ANTHROPIC_API_KEY=your_key_here

# Windows
set ANTHROPIC_API_KEY=your_key_here
```

Run the app:

```bash
# Windows (required for emoji output)
set PYTHONIOENCODING=utf-8
python grader.py
```

Then open `http://localhost:5000` in your browser.

---

## Project Structure

```
exam_grader/
├── grader.py            # Flask app — all routes and business logic
├── requirements.txt     # Dependencies
├── data/
│   ├── exam_grader.db   # SQLite: name↔ID mappings and grade data (local only)
│   ├── uploads/         # Anonymized exam PDFs
│   └── rubrics/         # Uploaded rubric files
└── templates/           # HTML templates (Bootstrap 5)
```

---

## Privacy Model

- The `data/` directory is excluded from version control (see `.gitignore`)
- Only anonymous IDs, exam content, and the rubric are transmitted to the Claude API
- Roster fuzzy matching runs entirely locally — no student names or SIDs touch the network
- Name-to-grade mapping happens locally after grading is complete

---

## License

MIT
