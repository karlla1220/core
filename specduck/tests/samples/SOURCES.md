3GPP CRs (public, from 3gpp.org), one per .doc reader fix that check_doc.py asserts:

| File | TDoc | What it holds |
|---|---|---|
| equations-with-revisions.doc | R5-205700 (RP-202239) | 39 equations stored as Word 2003 XML with tracked changes |
| visio-objects.doc | R3-202736 (RP-201091) | 4 Visio 2013 drawings beside Office 2010 metro blobs |
| pictures-after-equation-objects.doc | R5-202972 (RP-200581) | pictures right after Equation objects in table cells |
| non-breaking-hyphens.doc | R5-204477 (RP-201448) | non-breaking hyphens (TP-User-Data) |
| inserted-then-deleted.doc | R5-202914 (RP-200581) | text inserted by one revision and deleted by another |
| two-table-definitions.doc | R5-205489 (RP-202224) | table rows with two table definitions; rows starting after the grid's edge |
| tracked-paragraph-style.doc | R5-197049 (RP-191689) | headings inserted with track changes (style changed with sprmPIstd) |
| mathtype-object-in-quote.doc | R5-195443 (RP-190871) | a MathType equation written as { QUOTE … \| { EMBED Equation.DSMT4 } } |
| 38423-f50.zip | TS 38.423 V15.5.0 (archive zip) | clause 9.2.2.31: a run boundary between the two UTF-16 halves of 𝑳 (U+1D473) |
| word2007-equations-in-doc.doc | R5-195001 (RP-190871) | Word 2007 equations kept as pictures with their OMML in Word 2003 XML (wzEquationXML) |
