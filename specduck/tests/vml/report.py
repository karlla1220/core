"""report.py result.json OUT.html: every case with Word / x2t / .doc→Word / .doc→x2t crops and the differences."""
import base64, json, sys, html
import pymupdf
r = json.load(open(sys.argv[1]))
pdfs = {'word': pymupdf.open('vml-corpus.word.pdf'), 'x2t': pymupdf.open('vml-corpus.x2t.pdf'),
        'docword': pymupdf.open('vml-corpus.fromdoc.word.pdf'), 'docx2t': pymupdf.open('vml-corpus.fromdoc.x2t.pdf')}
def crop(name, clip):
    if not clip:
        return '<div class="empty">없음</div>'
    page = pdfs[name][clip[0]]
    rect = pymupdf.Rect(clip[1:]) & page.rect
    data = page.get_pixmap(clip=rect, dpi=96).tobytes('png')
    return f'<img src="data:image/png;base64,{base64.b64encode(data).decode()}" alt="">'
LABELS = {'x2t': 'x2t (docx)', 'docword': '.doc→x2t docx → Word', 'docx2t': '.doc→x2t docx → x2t'}
rows = []
for x in r:
    diffs = {n: x[n]['diff'] for n in LABELS}
    status = 'ok' if not any(diffs.values()) else 'bad'
    cells = [f'<figure><figcaption>Word</figcaption>{crop("word", x["word_clip"])}</figure>']
    for n, lab in LABELS.items():
        d = diffs[n]
        cells.append(f'<figure class="{"bad" if d else "ok"}"><figcaption>{lab}</figcaption>{crop(n, x[n]["clip"])}'
                     f'<ul>{"".join(f"<li>{html.escape(s)}</li>" for s in d) or "<li class=okli>같음</li>"}</ul></figure>')
    group = x['id'].split('-')[0]
    rows.append(f'<section class="case {status}" data-group="{group}" data-x2t="{int(bool(diffs["x2t"]))}" '
                f'data-docword="{int(bool(diffs["docword"]))}" data-docx2t="{int(bool(diffs["docx2t"]))}">'
                f'<h3><code>{html.escape(x["id"])}</code> <span>{html.escape(x["desc"])}</span></h3><div class="row">{"".join(cells)}</div></section>')
counts = {n: sum(1 for x in r if x[n]['diff']) for n in LABELS}
open(sys.argv[2], 'w').write(open('report_head.html').read().replace('{{TOTAL}}', str(len(r)))
    .replace('{{X2T}}', str(counts['x2t'])).replace('{{DOCWORD}}', str(counts['docword'])).replace('{{DOCX2T}}', str(counts['docx2t']))
    + ''.join(rows) + '</main><script>' + open('report.js').read() + '</script>')
