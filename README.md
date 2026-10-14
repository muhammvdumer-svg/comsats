# Management Sciences Timetable — COMSATS Islamabad

A simple static website for the Fall 2026 timetable of the Department of Management Sciences (effective 14 Sep 2026).

- Pick a program (BBA, BAF, BBD, BAT) and a section, then a day — today is selected by default and the class in progress is highlighted.
- Search across every section by course code, course name, teacher or room.
- Works on phones and supports dark mode.

## Deploy on Vercel

1. Go to [vercel.com/new](https://vercel.com/new) and import this repository.
2. Leave the framework preset as **Other** and click **Deploy** — there is no build step.

## Updating the timetable

All timetable data lives in `data.js`. It was generated from the department's PDF with the scripts in `scripts/`:

```bash
pip install pdfplumber
python3 scripts/parse.py timetable.pdf raw.json
python3 scripts/build.py raw.json data.js
```

The PDF layout changes from term to term, so check the output before publishing.
