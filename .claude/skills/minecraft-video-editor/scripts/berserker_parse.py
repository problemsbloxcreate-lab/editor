"""Parse BERSERKER ('Lava's') presets from Premiere's prfpset into a JSON catalog."""
import xml.etree.ElementTree as ET, json, sys
TICKS = 254016000000.0
t = ET.parse('presets.xml'); root = t.getroot()
byid = {el.get('ObjectID'): el for el in root if el.get('ObjectID')}

def nm(el):
    n = el.find('.//TreeItemBase/Name'); return n.text if n is not None else None

def kids(el):
    its = el.find('Items')
    return [byid[i.get('ObjectRef')] for i in its.findall('Item') if i.get('ObjectRef') in byid] if its is not None else []

def parse_param(p):
    o = {'name': (p.findtext('Name') or '').strip(), 'tv': p.findtext('IsTimeVarying') == 'true'}
    sk = p.findtext('StartKeyframe')
    cv = p.findtext('CurrentValue')
    o['cur'] = cv
    if sk: o['start'] = sk.split(',')[1] if ',' in sk else sk
    ks = (p.findtext('Keyframes') or '').strip()
    keys = []
    if ks:
        for k in ks.split(';'):
            k = k.strip()
            if not k: continue
            f = k.split(',')
            try: keys.append({'t': float(f[0]) / TICKS, 'v': f[1], 'interp': f[2] if len(f) > 2 else None, 'raw': k})
            except Exception: keys.append({'raw': k})
    if keys: o['keys'] = keys
    # ArrayParam / position (point) carry values in other tags
    return o

def parse_component(cid):
    vc = byid[cid]
    comp = vc.find('Component')
    o = {'match': vc.findtext('MatchName'), 'display': comp.findtext('DisplayName'), 'intrinsic': comp.findtext('Intrinsic'), 'params': []}
    ps = comp.find('Params')
    if ps is not None:
        for pr in ps.findall('Param'):
            r = pr.get('ObjectRef')
            if r in byid: o['params'].append(parse_param(byid[r]))
    return o

def parse_preset(el):
    data = el.find('.//Data')
    if data is None: return None
    d = byid.get(data.get('ObjectRef'))
    if d is None: return None
    out = {'filters': []}
    fps = d.find('FilterPresets')
    if fps is None: return out
    for fp in fps.findall('FilterPreset'):
        r = fp.get('ObjectRef'); f = byid.get(r)
        if f is None: continue
        cref = f.find('Component')
        entry = {'matchname': f.findtext('FilterMatchName'), 'in': f.findtext('AnchorInPoint'), 'out': f.findtext('AnchorOutPoint'), 'speed': f.findtext('Speed'), 'type': f.findtext('Type')}
        if cref is not None and cref.get('ObjectRef') in byid:
            entry['comp'] = parse_component(cref.get('ObjectRef'))
        out['filters'].append(entry)
    return out

cat = []
def walk(el, path):
    for k in kids(el):
        n = nm(k)
        if k.tag == 'BinTreeItem': walk(k, path + [n])
        else:
            pr = parse_preset(k)
            if pr is not None: cat.append({'path': path + [n], 'id': k.get('ObjectID'), **pr})
walk(byid['3'], ['Presets'])
json.dump(cat, open('presets_catalog.json', 'w', encoding='utf8'), ensure_ascii=False, indent=1)
print(len(cat), 'presets parsed')
