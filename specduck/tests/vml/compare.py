"""Compare renderings of vml-corpus against Word's, case by case.

Each PDF has one ``[case <id>]`` label per case; a case's region runs from below its label to the next label (or the
page end). From each region: the drawn box, path operators (lines, curves), stroke colours, widths and dash patterns,
fill colours, pictures, text and its direction, and an ink mask. Usage:
compare.py CASES.json REFERENCE.pdf NAME=OTHER.pdf[@REFERENCE2.pdf] ... > result.json
(a NAME with @REFERENCE2 is compared with that reference instead: the .doc paths with Word's rendering of the .doc,
since Word's own .doc writer already drops some VML, a -90 degree rotation among them)
"""
import json
import re
import sys

import numpy as np
import pymupdf

LABEL = re.compile(r'\[case ([^\]]+)\]')
DPI = 72


def regions(pdf: pymupdf.Document) -> dict[str, tuple[int, pymupdf.Rect]]:
    found = []
    for page in pdf:
        for block in page.get_text('dict')['blocks']:
            for line in block.get('lines', []):
                text = ''.join(s['text'] for s in line['spans'])
                m = LABEL.search(text)
                if m:
                    found.append((m.group(1), page.number, pymupdf.Rect(line['bbox'])))
    out = {}
    for i, (cid, pno, label) in enumerate(found):
        page = pdf[pno]
        bottom = page.rect.y1
        if i + 1 < len(found) and found[i + 1][1] == pno:
            bottom = found[i + 1][2].y0
        # Every case starts a page (the label is not a drawing): a rotated shape may reach above its label.
        top = page.rect.y0 if not (i and found[i - 1][1] == pno) else label.y0
        out[cid] = (pno, pymupdf.Rect(page.rect.x0, top, page.rect.x1, bottom - 0.5))
    return out


def hexcolor(c) -> str | None:
    if c is None:
        return None
    return '#%02x%02x%02x' % tuple(int(round(v * 255)) for v in c[:3])


def near(a: str, b: str, tol: int = 40) -> bool:
    x, y = int(a[1:], 16), int(b[1:], 16)
    return all(abs(((x >> s) & 255) - ((y >> s) & 255)) <= tol for s in (16, 8, 0))


def dash_ratio(dashes: str | None, width: float) -> tuple | None:
    """The dash array as multiples of the line width (None for solid)."""
    if not dashes:
        return None
    nums = [float(v) for v in re.findall(r'[\d.]+', dashes.split(']')[0])]
    if not nums or all(v == 0 for v in nums):
        return None
    w = width or 1
    return tuple(round(v / w, 1) for v in nums)


def drawn_rect(d) -> pymupdf.Rect:
    """The box of what a path draws: its curves sampled, not their control points (which its 'rect' takes)."""
    pts = []
    for it in d['items']:
        if it[0] == 'c':
            p0, p1, p2, p3 = it[1:5]
            for k in range(17):
                t = k / 16
                a, b, c, e = (1 - t) ** 3, 3 * (1 - t) ** 2 * t, 3 * (1 - t) * t * t, t ** 3
                pts.append(pymupdf.Point(a * p0.x + b * p1.x + c * p2.x + e * p3.x, a * p0.y + b * p1.y + c * p2.y + e * p3.y))
        elif it[0] == 're':
            pts += [it[1].tl, it[1].br]
        elif it[0] == 'qu':
            pts += [it[1].ul, it[1].ur, it[1].ll, it[1].lr]
        else:
            pts += [p for p in it[1:] if isinstance(p, pymupdf.Point)]
    if not pts:
        return d['rect']
    return pymupdf.Rect(min(p.x for p in pts), min(p.y for p in pts), max(p.x for p in pts), max(p.y for p in pts))


def features(pdf: pymupdf.Document, pno: int, region: pymupdf.Rect, label: str = '') -> dict:
    page = pdf[pno]
    box = None
    ops = {'l': 0, 'c': 0, 're': 0, 'qu': 0}
    strokes, fills, dashes, widths = set(), set(), set(), set()
    for d in page.get_drawings():
        half = max(d.get('width') or 0, 0.5) / 2      # a straight line's rect has no height
        r = drawn_rect(d) + (-half, -half, half, half)
        if not r.intersects(region) or r.y0 < region.y0 or r.y1 > region.y1 + 2:
            continue
        box = r if box is None else box | r
        for it in d['items']:
            ops[it[0]] = ops.get(it[0], 0) + 1
        if d.get('color') is not None and 's' in d['type']:
            strokes.add(hexcolor(d['color']))
            widths.add(round(d.get('width') or 0, 2))
            ratio = dash_ratio(d.get('dashes'), d.get('width') or 1)
            if ratio:
                dashes.add(ratio)
        if d.get('fill') is not None and 'f' in d['type']:
            fills.add(hexcolor(d['fill']))
    images = 0
    shape_box = box        # a picture fill is drawn clipped to its shape; its image box runs past the shape
    for info in page.get_image_info():
        r = pymupdf.Rect(info['bbox'])
        if r.intersects(region):
            images += 1
            if shape_box is not None and r.intersects(shape_box):
                r = r & (shape_box + (-2, -2, 2, 2))
            box = r if box is None else box | r
    texts, dirs = [], set()
    for block in page.get_text('dict', clip=region)['blocks']:
        for line in block.get('lines', []):
            t = ''.join(s['text'] for s in line['spans']).strip()
            if not t or LABEL.search(t) or t in label:     # a label's wrapped second line
                continue
            texts.append(t)
            dirs.add((round(line['dir'][0]), round(line['dir'][1])))
            r = pymupdf.Rect(line['bbox'])
            box = r if box is None else box | r
    ink = None
    if box is not None and not box.is_empty:
        clip = (box + (-2, -2, 2, 2)) & page.rect
        pix = page.get_pixmap(clip=clip, dpi=DPI, colorspace=pymupdf.csGRAY)
        ink = np.frombuffer(pix.samples, np.uint8).reshape(pix.height, pix.width) < 200
    return {'box': None if box is None else [round(box.width, 1), round(box.height, 1)], 'ops': ops,
            'strokes': sorted(c for c in strokes if c), 'fills': sorted(c for c in fills if c and c != '#ffffff'),
            'dashes': sorted(dashes), 'widths': sorted(widths), 'images': images,
            'text': ' '.join(texts), 'dirs': sorted(dirs), '_ink': ink, '_box': box, '_page': pno}


def iou(a, b) -> float | None:
    if a is None or b is None:
        return None
    h, w = max(a.shape[0], b.shape[0]), max(a.shape[1], b.shape[1])
    A = np.zeros((h, w), bool); B = np.zeros((h, w), bool)
    A[:a.shape[0], :a.shape[1]] = a; B[:b.shape[0], :b.shape[1]] = b
    def grow(m):
        g = m.copy()
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                g |= np.roll(np.roll(m, dy, 0), dx, 1)
        return g
    inter = (grow(A) & B).sum() + (A & grow(B)).sum()
    total = A.sum() + B.sum()
    return round(float(inter) / total, 3) if total else 1.0


def differences(ref: dict, got: dict) -> list[str]:
    out = []
    if got['box'] is None and ref['box'] is not None:
        return ['nothing drawn']
    if ref['box'] is None:
        return [] if got['box'] is None else ['drawn where Word draws nothing']
    (rw, rh), (gw, gh) = ref['box'], got['box']
    if abs(rw - gw) > max(4, rw * 0.06) or abs(rh - gh) > max(4, rh * 0.06):
        out.append(f'size {gw}x{gh} (Word {rw}x{rh})')
    if ref['ops']['c'] + ref['ops']['qu'] > 0 and got['ops']['c'] + got['ops']['qu'] == 0:
        out.append('curves missing')
    if ref['ops']['c'] == 0 and got['ops']['c'] > 4 and ref['ops']['l'] + ref['ops']['re'] > 0:
        out.append('curves where Word has straight lines')
    if bool(ref['dashes']) != bool(got['dashes']):
        out.append('dashed' if got['dashes'] else 'solid where Word is dashed')
    elif ref['dashes'] and not any(all(abs(x - y) <= max(0.6, 0.35 * x) for x, y in zip(r, g)) and len(r) == len(g)
                                   for r in ref['dashes'] for g in got['dashes']):
        out.append(f'dash pattern {got["dashes"]} (Word {ref["dashes"]})')
    miss = [c for c in ref['fills'] if not any(near(c, g) for g in got['fills'])]
    if miss and not (ref['images'] or got['images']):
        out.append(f'fill colours missing {miss}')
    miss = [c for c in ref['strokes'] if not any(near(c, g) for g in got['strokes'])]
    if miss:
        out.append(f'stroke colours missing {miss}')
    score = iou(ref['_ink'], got['_ink'])
    # Word puts some vector drawing into its PDF as pictures (a pattern as hundreds of tiles, vertical text in a group,
    # a transparent shadow): a picture count tells only when the drawing differs too
    if ref['images'] != got['images'] and (score is None or score < 0.75) and (ref['images'] <= 3 or got['images'] == 0):
        out.append(f'pictures {got["images"]} (Word {ref["images"]})')
    norm = lambda t: re.sub(r'\s+', '', t)
    if norm(ref['text']) != norm(got['text']):
        out.append(f'text "{got["text"][:40]}" (Word "{ref["text"][:40]}")')
    if ref['dirs'] != got['dirs'] and ref['text']:
        out.append(f'text direction {got["dirs"]} (Word {ref["dirs"]})')
    if score is not None and score < 0.75:
        out.append(f'ink overlap {score}')
    return out


def main() -> None:
    cases = json.load(open(sys.argv[1]))
    ref_pdf = pymupdf.open(sys.argv[2])
    refs = {sys.argv[2]: ref_pdf}
    others = []
    for a in sys.argv[3:]:
        name, files = a.split('=', 1)
        path, _, ref = files.partition('@')
        ref = ref or sys.argv[2]
        refs.setdefault(ref, pymupdf.open(ref))
        others.append((name, pymupdf.open(path), ref))
    ref_regions = {ref: regions(pdf) for ref, pdf in refs.items()}
    other_regions = {name: regions(pdf) for name, pdf, _ in others}
    result = []
    for case in cases:
        cid = case['id']
        row = {'id': cid, 'desc': case['desc']}
        feats = {}
        for path, pdf in refs.items():
            if cid in ref_regions[path]:
                feats[path] = features(pdf, *ref_regions[path][cid], case['desc'])
        if sys.argv[2] not in feats:
            row['word'] = 'no label'
            result.append(row)
            continue
        ref = feats[sys.argv[2]]
        row['word'] = {k: v for k, v in ref.items() if not k.startswith('_')}
        row['word_clip'] = [ref['_page'], *(ref['_box'] + (-4, -4, 4, 4))] if ref['_box'] else None
        for name, pdf, refpath in others:
            ref = feats.get(refpath)
            if ref is None:
                row[name] = {'diff': ['reference case missing']}
                continue
            if cid not in other_regions[name]:
                row[name] = {'diff': ['case missing']}
                continue
            skip = case.get('skip', {})
            if name in skip or '*' in skip:
                row[name] = {'diff': [], 'skipped': skip.get(name, skip.get('*')), 'clip': None}
                continue
            got = features(pdf, *other_regions[name][cid], case['desc'])
            row[name] = {k: v for k, v in got.items() if not k.startswith('_')}
            row[name]['diff'] = differences(ref, got)
            row[name]['clip'] = [got['_page'], *(got['_box'] + (-4, -4, 4, 4))] if got['_box'] else None
        result.append(row)
    json.dump(result, sys.stdout, indent=1, default=list)


main()
