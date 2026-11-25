"""Check x2t's VML against Word: render the corpus with the x2t given and compare it with Word's PDFs, case by case.

Usage: check_vml.py <x2t binary of an installed x2t (fonts and sdkjs beside it)> [work dir]
Renders vml-corpus.docx (Word's own VML, read by x2t) and vml-corpus.doc (Word's .doc of it: x2t's .doc writer, then
its reader) to PDF, compares them with vml-corpus.word.pdf and vml-corpus.doc.word.pdf (compare.py), and fails on any
difference that expected.json does not list with its reason. Word is not needed: its PDFs are committed (refs.sh
remakes them on a Mac with Word). Needs pymupdf and numpy.
"""
import json
import re
import subprocess
import zipfile
from collections import Counter
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).parent


def x2t(binary: Path, src: Path, dst: Path, fmt: int) -> None:
    task = dst.with_suffix('.task.xml')
    task.write_text('<?xml version="1.0" encoding="utf-8"?><TaskQueueDataConvert>'
                    f'<m_sFileFrom>{src}</m_sFileFrom><m_sFileTo>{dst}</m_sFileTo>'
                    f'<m_nFormatTo>{fmt}</m_nFormatTo></TaskQueueDataConvert>')
    subprocess.run([str(binary), str(task)], check=True, timeout=600, capture_output=True)


def repeated_shapetypes(docx: Path) -> list[str]:
    """Shapetypes written more than once in one part of x2t's docx of a .doc (its writer puts each before its first
    shape, once); the picture frame's _x0000_t75 goes with every picture, as before specDuck."""
    out = []
    with zipfile.ZipFile(docx) as z:
        for name in z.namelist():
            if name.startswith('word/') and name.endswith('.xml'):
                ids = Counter(re.findall(r'<v:shapetype [^>]*\bid="([^"]+)"', z.read(name).decode('utf-8', 'replace')))
                out += [f'{name}: {i} x{n}' for i, n in ids.items() if n > 1 and i != '_x0000_t75']
    return out


def main() -> int:
    binary = Path(sys.argv[1]).resolve()
    work = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(tempfile.mkdtemp(prefix='vml-'))
    work.mkdir(parents=True, exist_ok=True)
    x2t(binary, HERE / 'vml-corpus.docx', work / 'x2t.pdf', 513)
    x2t(binary, HERE / 'vml-corpus.doc', work / 'fromdoc.docx', 65)
    x2t(binary, work / 'fromdoc.docx', work / 'fromdoc.pdf', 513)
    repeated = repeated_shapetypes(work / 'fromdoc.docx')
    out = subprocess.run([sys.executable, str(HERE / 'compare.py'), str(HERE / 'vml-corpus.cases.json'),
                          str(HERE / 'vml-corpus.word.pdf'), f'x2t={work / "x2t.pdf"}',
                          f'docx2t={work / "fromdoc.pdf"}@{HERE / "vml-corpus.doc.word.pdf"}'],
                         check=True, capture_output=True, text=True).stdout
    (work / 'result.json').write_text(out)
    expected = json.loads((HERE / 'expected.json').read_text())
    new, gone = [], []
    for row in json.loads(out):
        for path in ('x2t', 'docx2t'):
            diff = row.get(path, {}).get('diff', [])
            known = expected.get(row['id'], {}).get(path)
            if diff and not known:
                new.append(f'{row["id"]} ({path}): {"; ".join(diff)}')
            elif known and not diff:
                gone.append(f'{row["id"]} ({path})')
    for line in new:
        print('NEW  ' + line)
    for line in repeated:
        print('SHAPETYPE WRITTEN TWICE  ' + line)
    for line in gone:
        print('now same as Word (drop from expected.json): ' + line)
    print(f'{len(new)} new differences; result in {work / "result.json"}')
    return 1 if new or repeated else 0


if __name__ == '__main__':
    sys.exit(main())
