#!/bin/sh
# Build COVER_LETTER.docx from COVER_LETTER_DRAFT.md.
#
# Only the letter itself goes into the .docx: the part between the first and
# second horizontal rules. Everything above the first rule is instruction to
# VD, everything below the second is the record of what the letter does and
# does not claim, and neither belongs in a file an editor reads.
#
#   sh make_cover_letter.sh [DIR]      default DIR is _stage_plos
set -e
HERE=$(cd "$(dirname "$0")" && pwd)
DIR="${1:-${PLOS_DEST:-$HERE/_stage_plos}}"
if ! command -v pandoc >/dev/null 2>&1; then
  echo "make_cover_letter.sh: pandoc is not installed; the .docx cannot be built." >&2
  echo "  macOS: brew install pandoc" >&2
  exit 2
fi
if [ ! -f "$DIR/COVER_LETTER_DRAFT.md" ]; then
  echo "make_cover_letter.sh: not found: $DIR/COVER_LETTER_DRAFT.md" >&2
  exit 2
fi
SRC="$DIR/COVER_LETTER_DRAFT.md"
BODY="$DIR/_cover_body.md"
awk 'BEGIN{n=0} /^---$/{n++; next} n==1{print}' "$SRC" > "$BODY"
test -s "$BODY"
grep -q 'Dear Editors' "$BODY"
grep -q 'Yours sincerely' "$BODY"
! grep -q 'Notes on what is and is not claimed' "$BODY"
pandoc -f markdown -t docx -o "$DIR/COVER_LETTER.docx" "$BODY"
printf 'wrote %s (%s words, %s bytes)\n' "$DIR/COVER_LETTER.docx" \
  "$(wc -w < "$BODY" | tr -d ' ')" "$(wc -c < "$DIR/COVER_LETTER.docx" | tr -d ' ')"
