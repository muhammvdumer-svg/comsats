import json, re, sys
S = json.load(open(sys.argv[1]))
TIME_RE = re.compile(r'^(\d{3,4})\s*-+\s*(\d{3,4})\s*(.*)$')
def hm(t): t=t.zfill(4); return f"{t[:2]}:{t[2:]}"
def norm(s): return re.sub(r'[^a-z0-9]', '', s.lower())
out = []
ALL = [c for s0 in S for c in s0['courses'] if c['code'] and c['instructor']]
for s in S:
    sess = []
    for x in s['sessions']:
        m = TIME_RE.match(x['course'])
        if m and sess:  # continuation cell holding only a time: repeat previous course on that day
            prev = next((p for p in reversed(sess) if p['day'] == x['day']), sess[-1])
            x = dict(prev, start=hm(m.group(1)), end=hm(m.group(2)), room=x['note'], note=m.group(3))
        note = x['note'].strip()
        note = re.sub(r'^\((.*)\)$', r'\1', note).strip()
        if note in ('A', 'B', 'C'): note = f'Grp. {note}'
        if note in ('Fin.',): note = 'Finance'
        x['note'] = note
        sess.append(x)
    if s['name'] == 'BBA-5ab':
        for room in ('210', '230'):
            sess.append(dict(day='Friday', course='Elective I (Finance) FIN471 - Islamic Banking and Finance', code='FIN471',
                             start='08:30', end='11:30', room=room, note='', group=''))
    courses = [c for c in s['courses'] if c['title'] and c['title'] not in ('N/A', 'Online Classes') and not c['title'].startswith('100 Students')]
    for c in courses:
        c['title'] = c['title'].replace(' Online Classes', '').strip()
        if not c['instructor']: c['instructor'] = 'TBA'
    for x in sess:
        hits = [c for c in courses if x['code'] and c['code'] == x['code']]
        if not hits:
            key = norm(re.sub(r'^.*?\)\s*', '', x['course']) if ')' in x['course'] else x['course'])
            hits = [c for c in courses if key and key in norm(c['title'])]
        if not hits and x['code']:
            alt = x['code'].replace('MGT475', 'MKT475')
            hits = [c for c in ALL if c['code'] == alt][:2]
        g = re.search(r'Section\s*([A-Z])', x.get('group', ''))
        if g:
            narrowed = [c for c in hits if re.sub(r'[^A-Za-z0-9]', '', c['id']).upper().endswith(g.group(1)) and not re.sub(r'[^A-Za-z0-9]', '', c['id']).upper().endswith('AB')]
            if narrowed: hits = narrowed
            elif hits and len(re.findall(r'[A-Z]{3}\s?\d{3}', x['course'])) <= 2 and all(re.sub(r'[^A-Za-z0-9]', '', c['id']).upper().endswith('AB') for c in hits):
                x['group'] = ''  # shared elective for both sections
        names = []
        for c in hits:
            n = c['instructor']
            if c['credits'].upper() == 'LAB' and n not in names: n = f"{n} (Lab)"
            if n not in names and n.replace(' (Lab)', '') not in names: names.append(n)
        x['instructor'] = ', '.join(names) or 'TBA'
        if len(re.findall(r'[A-Z]{3}\s?\d{3}', x['course'])) > 2: x['instructor'] = 'Several electives — see course list'
        x['course'] = re.sub(r'\s+', ' ', x['course'])
        for k in ('code',): x.pop(k, None)
        if not x['group']: x.pop('group')
        if not x['note']: x.pop('note')
    out.append(dict(program=s['program'], intake=s['intake'], section=s['section'], name=s['name'],
                    sessions=sess, courses=[dict(id=c['id'], title=c['title'], credits=c['credits'], instructor=c['instructor']) for c in courses]))
missing = [(o['name'], x['course']) for o in out for x in o['sessions'] if not x['instructor'] or not x['start']]
print('missing:', missing)
open(sys.argv[2], 'w').write('window.TIMETABLE = ' + json.dumps(dict(title='Department of Management Sciences — Fall 2026', effective='14 Sep 2026', sections=out), separators=(',', ':')) + ';\n')
