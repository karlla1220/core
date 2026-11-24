#!/bin/bash
# Word's references for vml-corpus.docx: its PDF, its .doc, and its PDF of that .doc; then send both inputs to the server.
set -eo pipefail
cd "$(dirname "$0")"
C=${WORD_DIR:-$HOME/Library/Containers/com.microsoft.Word/Data/sdvg}; mkdir -p $C
uv run -q --with pillow python make_corpus.py vml-corpus.docx
cp vml-corpus.docx $C/ && rm -f $C/vml-corpus.doc
osascript -e "tell application \"Microsoft Word\"
open file name \"$C/vml-corpus.docx\"
save as active document file name \"$C/vml-corpus.word.pdf\" file format format PDF
close every document saving no
open file name \"$C/vml-corpus.docx\"
save as active document file name \"$C/vml-corpus.doc\" file format format document97
close every document saving no
open file name \"$C/vml-corpus.doc\"
save as active document file name \"$C/vml-corpus.doc.word.pdf\" file format format PDF
close every document saving no
end tell"
cp $C/vml-corpus.word.pdf $C/vml-corpus.doc.word.pdf $C/vml-corpus.doc .
[ -n "${SEND_TO:-}" ] && scp -q vml-corpus.docx vml-corpus.doc "$SEND_TO"
