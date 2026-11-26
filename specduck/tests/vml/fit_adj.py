"""Fit how Word turns a legacy shape's VML adj values into its DrawingML preset's avLst, from adjlearn.docx.

adjlearn.docx holds, per legacy autoshape type and per size (120x60, 60x120), a shape with default adjustments and one
per adjustment set to 0.15 and 0.3. Word writes each as wps (prstGeom + avLst) with a VML fallback (adj). For every
DrawingML guide we look for the VML adj index and the form dml = a * vml * F(w, h) + b (F among 1, w/ss, h/ss, ...)
that reproduces every sample. Writes adjfit.json: {spt: {"prst": name, "gd": {gdname: [index, form, a, b]}}}.
"""
import json
import re
import sys
import zipfile
from collections import defaultdict

import glob
SRCS = sys.argv[1:] or sorted(glob.glob('/Users/karlla/Library/Containers/com.microsoft.Word/Data/sdvg/adj-*.docx'))
d = ''.join(zipfile.ZipFile(p).read('word/document.xml').decode() for p in SRCS)
types = {m.group(1): m.group(0) for m in re.finditer(r'<v:shapetype [^>]*id="_x0000_t(\d+)"[^>]*>', d)}



def vml_adj(shape: str, spt: str) -> list[float | None]:
    own = re.search(r' adj="([^"]*)"', shape)
    st = re.search(r' adj="([^"]*)"', types.get(spt, ''))
    base = [v for v in (st.group(1).split(',') if st else [])]
    vals = own.group(1).split(',') if own else []
    out = []
    for i in range(max(len(base), len(vals))):
        v = vals[i] if i < len(vals) and vals[i] != '' else (base[i] if i < len(base) else '')
        out.append(float(v.rstrip('f')) if v not in ('', None) else None)
    return out


samples = defaultdict(list)    # spt -> [(prst, w, h, vml list, dml dict)]
for ac in re.findall(r'<mc:AlternateContent>(.*?)</mc:AlternateContent>', d, re.S):
    prst = re.search(r'<a:prstGeom prst="(\w+)"', ac)
    if not prst:
        continue
    ext = re.search(r'<a:ext cx="(\d+)" cy="(\d+)"', ac)
    w, h = int(ext.group(1)), int(ext.group(2))
    gds = {g: int(v) for g, v in re.findall(r'<a:gd name="(\w+)" fmla="val (-?\d+)"', ac)}
    fb = ac.split('<mc:Fallback>')[1]
    for m in re.finditer(r'<v:shapetype [^>]*id="_x0000_t(\d+)"[^>]*>', fb):
        types.setdefault(m.group(1), m.group(0))
    sh = re.search(r'<v:shape [^>]*>', fb)
    if not sh:
        continue
    spt = re.search(r'type="#_x0000_t(\d+)"', sh.group(0))
    if not spt:
        continue
    samples[spt.group(1)].append((prst.group(1), w, h, vml_adj(sh.group(0), spt.group(1)), gds))

FORMS = {
    '1': lambda w, h: 1.0, 'w/ss': lambda w, h: w / min(w, h), 'h/ss': lambda w, h: h / min(w, h),
    'ss/w': lambda w, h: min(w, h) / w, 'ss/h': lambda w, h: min(w, h) / h, 'w/h': lambda w, h: w / h,
    'h/w': lambda w, h: h / w,
}

result, unfitted = {}, []
for spt, rows in sorted(samples.items(), key=lambda kv: int(kv[0])):
    prst = rows[0][0]
    names = sorted({g for r in rows for g in r[4]})
    entry = {'prst': prst, 'gd': {}}
    for g in names:
        pts = [(r[1], r[2], r[3], r[4][g]) for r in rows if g in r[4]]
        best = None
        if len({y for *_, y in pts}) == 1:          # a guide Word writes as a constant (hexagon vf)
            entry['gd'][g] = [-1, '1', 0, float(pts[0][3])]
            continue
        nadj = max(len(r[3]) for r in rows)
        for i in range(nadj):
            usable = [(w, h, v[i], y) for w, h, v, y in pts if i < len(v) and v[i] is not None]
            if len(usable) < 3:
                continue
            for name, f, scaled in [(n, f, s) for n, f in FORMS.items() for s in (False, True)]:
                # scaled: dml = (a * vml + b) * F, else dml = a * vml * F + b
                xs = [v for w, h, v, _ in usable] if scaled else [v * f(w, h) for w, h, v, _ in usable]
                ys = [y / f(w, h) for w, h, _, y in usable] if scaled else [y for *_, y in usable]
                n = len(xs)
                mx, my = sum(xs) / n, sum(ys) / n
                sxx = sum((x - mx) ** 2 for x in xs)
                if sxx == 0:
                    continue
                a = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sxx
                b = my - a * mx
                fs = [f(w, h) for w, h, _, _ in usable] if scaled else [1] * n
                err = max(abs((a * x + b - y) * k) for x, y, k in zip(xs, ys, fs))
                if best is None or err < best[0]:
                    best = (err, i, ('*' if scaled else '') + name, a, b)
        if best and best[0] <= max(300, 0.01 * max(abs(p[3]) for p in pts)):
            entry['gd'][g] = [best[1], best[2], round(best[3], 6), round(best[4], 1)]
        else:
            unfitted.append((spt, prst, g, best and round(best[0])))
    if any(u[0] == spt for u in unfitted):
        continue        # a guide Word does not derive this way: the shape keeps its path geometry
    result[spt] = entry
json.dump(result, open('adjfit.json', 'w'), indent=0)
print(len(result), 'types;', sum(len(e['gd']) for e in result.values()), 'guides fitted;', len(unfitted), 'not:')
for u in unfitted:
    print('  ', u)
