"""Silêncios de fala na timeline (VAD de todas as vozes da fonte) — lista os vãos > LIM s."""
import json, sys
LIM = float(sys.argv[1]) if len(sys.argv) > 1 else 0.4
P = json.load(open(sys.argv[2] if len(sys.argv) > 2 else 'plan.json', encoding='utf8'))
V = json.load(open('vad.json'))
TR = {'A': ['A1', 'A3'], 'C': ['C1', 'C3'], 'B': ['B1']}
sp = []
for k in P['keeps']:
    if k['seg'] == 'endbg': continue
    for tr in TR[k['src']]:
        for s, e in V[tr]:
            a, b = max(s, k['src_in']), min(e, k['src_out'])
            if b > a: sp.append((k['tl_in'] + a - k['src_in'], k['tl_in'] + b - k['src_in']))
sp.sort()
m = []
for s, e in sp:
    if m and s <= m[-1][1] + 0.01: m[-1][1] = max(m[-1][1], e)
    else: m.append([s, e])
end = max(k['tl_out'] for k in P['keeps'] if k['seg'] != 'endbg')
gaps = [(m[i][1], m[i + 1][0]) for i in range(len(m) - 1) if m[i + 1][0] - m[i][1] > LIM]
if m[0][0] > LIM: gaps.insert(0, (0, m[0][0]))
def seg_at(t):
    for k in P['keeps']:
        if k['tl_in'] <= t < k['tl_out']: return k
tot = sum(b - a for a, b in gaps)
print('vãos > %.2f s: %d, total %.1f s de %.1f' % (LIM, len(gaps), tot, end))
import collections
by = collections.Counter()
for a, b in gaps:
    k = seg_at((a + b) / 2); by[k['seg']] += b - a
    if '-v' in sys.argv: print('%8.2f %5.2f  %s %s %.2f' % (a, b - a, k['seg'], k['src'], k['src_in'] + (a - k['tl_in'])))
print(sorted(by.items(), key=lambda x: -x[1])[:25])
