# VML corpus

Every VML element and attribute Word writes (and those found in 3GPP specifications and TDocs, `vml_inventory.py`),
one case per page of `vml-corpus.docx`, rendered by Word for Mac as the reference. `check_vml.py <x2t>` renders the
corpus with x2t, both from the docx and through Word's `.doc` of it, and compares each case with Word's PDF:
`expected.json` lists the differences known and why (most are sdkjs, which draws what x2t hands it).

| File | What |
|---|---|
| `make_corpus.py` | writes `vml-corpus.docx` and `vml-corpus.cases.json` (cases, and the ones not judged on a path: `SKIP`) |
| `shapetypes.json`, `word-wdUpDiag.gif` | Word's own legacy shapetypes and pattern bitmap, which the corpus uses |
| `refs.sh` | on a Mac with Word: remakes the corpus, Word's PDF of it, its `.doc` and Word's PDF of that `.doc` |
| `compare.py` | per case: drawn box, curves, dashes, colours, pictures, text and its direction, ink overlap |
| `check_vml.py` | the check; `report.py` turns its result into a page with every case side by side |
| `fit_adj.py`, `gen_preset_header.py` | Word's VML adj → preset guides, from shapes Word made (`WordPresetGeometry.h`) |
| `patterns.json` | Word's VML pattern bitmaps per DrawingML preset |

The `.doc` path is compared with Word's rendering of the `.doc` (Word's own `.doc` writer already drops a -90° rotation
and a horizontal rule), the docx path with Word's rendering of the docx.
