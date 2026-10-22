import json, sys
sys.stdout.reconfigure(encoding='utf8')
W = r'C:\Users\mathe\Skills\_research\mc-test\work'
a, b = float(sys.argv[1]), float(sys.argv[2])
ws = []
for k, n in (('t1', 'A'), ('t2', 'B')):
    for w in json.load(open(W + '\%s.json' % k, encoding='utf8'))['words']:
        if a <= w['s'] < b: ws.append((w['s'], w['e'], n, w['w'].strip()))
ws.sort()
cur = None; line = ''; st = 0; last = 0
for s, e, n, w in ws:
    if cur != n or s - last > 1.2:
        if line: print('%6.1f %s: %s' % (st, cur, line))
        cur, line, st = n, '', s
    line += w + ' '; last = e
if line: print('%6.1f %s: %s' % (st, cur, line))
