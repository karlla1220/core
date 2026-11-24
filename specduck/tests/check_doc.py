"""Regression check of specDuck's .doc reader fixes: converts each sample .doc with the x2t given and asserts what Word
shows (checked against Word for Mac). Usage: check_doc.py <x2t> <samples dir>. Exits non-zero on the first failure.

Every file: no UserStyle_ ids, no highlight "auto", no formatting a reader shows set twice in one w:rPr (the first
would be read), every equation has text, and every table row's gridBefore + spans + gridAfter fills the grid. Then one
case per fix (CASES)."""
import re
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
M = '{http://schemas.openxmlformats.org/officeDocument/2006/math}'
# Run formatting that changes what a reader shows; a duplicate of anything else (snapToGrid) changes nothing read.
SHOWN = {W + t for t in ('b', 'i', 'u', 'strike', 'dstrike', 'highlight', 'color', 'vertAlign', 'shd', 'vanish',
                         'caps', 'smallCaps')}


def convert(x2t: Path, doc: Path, work: Path) -> Path:
    src, dst = work / 'in.doc', work / 'out.docx'
    if doc.suffix == '.zip':        # a specification as 3GPP publishes it: its one .doc
        with zipfile.ZipFile(doc) as z:
            src.write_bytes(z.read(next(n for n in z.namelist() if n.lower().endswith('.doc'))))
    else:
        src.write_bytes(doc.read_bytes())
    task = work / 'task.xml'
    task.write_text('<?xml version="1.0" encoding="utf-8"?><TaskQueueDataConvert>'
                    f'<m_sFileFrom>{src}</m_sFileFrom><m_sFileTo>{dst}</m_sFileTo>'
                    '<m_nFormatTo>65</m_nFormatTo></TaskQueueDataConvert>')
    subprocess.run([str(x2t), str(task)], check=True, timeout=120, capture_output=True,
                   env={'LD_LIBRARY_PATH': str(x2t.parent)})
    return dst


def int_val(el, name):
    child = el.find(name) if el is not None else None
    return int(child.get(W + 'val')) if child is not None else 0


def common(name: str, docx: Path) -> list[str]:
    z = zipfile.ZipFile(docx)
    xml, styles = z.read('word/document.xml').decode(), z.read('word/styles.xml').decode()
    errs = []
    if 'UserStyle_' in styles:
        errs.append('UserStyle_ style ids')
    if 'w:highlight w:val="auto"' in xml:
        errs.append('highlight "auto"')
    root = ET.fromstring(xml)
    for rpr in root.iter(W + 'rPr'):
        tags = [c.tag for c in rpr if c.tag in SHOWN]
        if len(tags) != len(set(tags)):
            errs.append('shown formatting twice in one w:rPr')
            break
    if any(not ''.join(t.text or '' for t in m.iter(M + 't')).strip() for m in root.iter(M + 'oMath')):
        errs.append('an equation without text')
    for tbl in root.iter(W + 'tbl'):
        cols = len(tbl.find(W + 'tblGrid')) if tbl.find(W + 'tblGrid') is not None else 0
        for tr in tbl.findall(W + 'tr'):
            pr = tr.find(W + 'trPr')
            total = int_val(pr, W + 'gridBefore') + int_val(pr, W + 'gridAfter') + sum(
                max(1, int_val(tc.find(W + 'tcPr'), W + 'gridSpan')) for tc in tr.findall(W + 'tc'))
            if cols and total != cols:
                errs.append(f'a table row spans {total} of {cols} grid columns')
                break
        else:
            continue
        break
    return [f'{name}: {e}' for e in errs]


def text(xml: str) -> str:
    return ''.join(re.findall(r'<w:t[^>]*>([^<]*)</w:t>', xml))


# file: (what Word shows, check on document.xml)
CASES = {
    'equations-with-revisions.doc': ('39 equations, each with its text (aml annotations, Word 2003 run properties)',
                                     lambda x: x.count('<m:oMath>') == 39),
    'visio-objects.doc': ('4 Visio objects keep ProgID Visio.Drawing.15',
                          lambda x: x.count('ProgID="Visio.Drawing.15"') == 4),
    'pictures-after-equation-objects.doc': ('12 pictures beside 8 equation objects (each picture after an object)',
                                            lambda x: (x.count('<w:pict'), x.count('<w:object')) == (12, 8)),
    'non-breaking-hyphens.doc': ('TP-User-Data keeps its hyphens', lambda x: x.count('<w:noBreakHyphen/>') > 0),
    'inserted-then-deleted.doc': ('text inserted then deleted: w:ins around w:del',
                                  lambda x: re.search(r'<w:ins [^>]*><w:del ', x) is not None),
    'two-table-definitions.doc': ('cells read the table definition in force (rows fill the grid)', lambda x: True),
    'mathtype-object-in-quote.doc': ('the MathType object inside a QUOTE field keeps its ProgID and storage',
                                     lambda x: 'ProgID="Equation.DSMT4"' in x and 'ObjectID="_0"' not in x),
    'word2007-equations-in-doc.doc': ('17 Word 2007 equations come back as m:oMath, none as a "Word.Document" package',
                                      lambda x: x.count('<m:oMath>') == 17 and 'ProgID="Word.Document"' not in x),
    '38423-f50.zip': ('a character outside the BMP split over two runs stays one (U+1D473, no lone surrogate)',
                      lambda x: '\U0001d473' in x and '\U0001d400' not in x
                      and not re.search('[\ud800-\udfff]', x)),
    'tracked-paragraph-style.doc': ('an inserted heading keeps its new style',
                                    lambda x: re.search(r'<w:pStyle w:val="Heading1"/>(?:(?!</w:p>).)*Scope', x,
                                                        re.S) is not None),
}


def main() -> int:
    x2t, samples = Path(sys.argv[1]).resolve(), Path(sys.argv[2])
    failures = []
    for name, (what, check) in CASES.items():
        with tempfile.TemporaryDirectory() as work:
            try:
                docx = convert(x2t, samples / name, Path(work))
            except Exception as exc:  # noqa: BLE001 - reported below
                failures.append(f'{name}: x2t failed: {exc}')
                continue
            try:
                zipfile.ZipFile(docx).read('word/document.xml').decode()
            except UnicodeDecodeError as exc:   # a lone surrogate written as CESU-8
                failures.append(f'{name}: document.xml is no valid UTF-8 ({exc.reason} at byte {exc.start})')
                print('FAIL ' + name)
                continue
            failures += common(name, docx)
            if not check(zipfile.ZipFile(docx).read('word/document.xml').decode()):
                failures.append(f'{name}: {what}')
        print(('FAIL ' if any(f.startswith(name) for f in failures) else 'ok   ') + name)
    for f in failures:
        print('  ' + f)
    return 1 if failures else 0


if __name__ == '__main__':
    sys.exit(main())
