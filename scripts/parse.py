import pdfplumber, re, json, sys
pdf = pdfplumber.open(sys.argv[1])
DAYS = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday"]
TITLE_RE = re.compile(r'(Fall|Spring|Fall/Spring)\s+(\d{4})\s*-\s*([A-Z]{3})\s*-\s*(.+)')
TIME_RE = re.compile(r'(\d{3,4})\s*-+\s*(\d{3,4})')
CODE_RE = re.compile(r'\b([A-Z]{3})\s?-?(\d{3})\b')

def hm(t):
    t = t.zfill(4); return f"{t[:2]}:{t[2:]}"

def clean(s): return re.sub(r'\s+', ' ', (s or '').replace('\n', ' ')).strip()

sections = []
for pi, page in enumerate(pdf.pages):
    tables = page.find_tables()
    # instructor lines: words on page grouped by line
    words = page.extract_words(keep_blank_chars=False, use_text_flow=False, extra_attrs=["size"])
    lines = {}
    for w in words:
        key = round(w['top'] / 2)
        lines.setdefault(key, []).append(w)
    linelist = sorted(lines.items())
    for tb in tables:
        t = tb.extract()
        if not t or not t[0] or len(t) < 3: continue
        title = next((c for c in t[0] if c), None)
        m = TITLE_RE.search(clean(title or ''))
        if not m: continue
        program, sec = m.group(3), clean(m.group(4))
        name = f"{program}-{sec.replace(' ', '')}"
        sessions = []
        group = ''
        rows = t[2:]
        i = 0
        while i + 2 < len(rows) + 0 and i < len(rows):
            r = rows[i]
            if r[0] and r[0].startswith('Course ID'): break
            if i + 2 >= len(rows): break
            tr, rr = rows[i+1], rows[i+2]
            label = clean(r[0])
            if label.lower().startswith('section'):
                group = label.replace(' - ', ' ')
            lt = TIME_RE.search(label)
            for d in range(6):
                c = d + 1
                if c >= len(r): continue
                course = clean(r[c])
                if not course: continue
                tline = clean(tr[c] if c < len(tr) else '')
                room = clean(rr[c] if c < len(rr) else '')
                tm = TIME_RE.search(tline) or lt
                start = end = None
                if tm: start, end = hm(tm.group(1)), hm(tm.group(2))
                note = tline
                if tm and tm is not lt: note = tline.replace(tm.group(0), '')
                note = re.sub(r'\(\s*\d\s*hrs?\.?\s*\)', '', note, flags=re.I).strip()
                if re.fullmatch(r'AB-\d', note):
                    if 'AB-' not in room: room = f"{room} ({note})".strip()
                    note = ''
                cm = CODE_RE.search(course)
                sessions.append(dict(day=DAYS[d], course=course, code=(cm.group(1)+cm.group(2)) if cm else '',
                                     start=start, end=end, room=room, note=note, group=group))
            i += 3
        # instructor list: lines below table bottom until next 'Department' line
        bottom = tb.bbox[3]
        instr = []
        for key, ws in linelist:
            top = min(w['top'] for w in ws)
            if top < bottom - 2: continue
            txt = ' '.join(w['text'] for w in sorted(ws, key=lambda w: w['x0']))
            if txt.startswith('Department of Management') : break
            if txt.startswith('Time Table') or 'Course ID' in txt: continue
            ws = sorted(ws, key=lambda w: w['x0'])
            idp = ' '.join(w['text'] for w in ws if w['x0'] < 90)
            ttl = ' '.join(w['text'] for w in ws if 90 <= w['x0'] < 335)
            cr = ' '.join(w['text'] for w in ws if 335 <= w['x0'] < 395)
            ins = ' '.join(w['text'] for w in ws if 395 <= w['x0'] < 470)
            if not ttl: continue
            cm = CODE_RE.search(ttl)
            instr.append(dict(id=idp, title=ttl, credits=cr, instructor=ins, code=(cm.group(1)+cm.group(2)) if cm else ''))
        sections.append(dict(program=program, intake=f"{m.group(1)} {m.group(2)}", section=sec, name=name,
                             page=pi+1, sessions=sessions, courses=instr))
json.dump(sections, open(sys.argv[2], 'w'), indent=1)
print(len(sections), sum(len(s['sessions']) for s in sections))
