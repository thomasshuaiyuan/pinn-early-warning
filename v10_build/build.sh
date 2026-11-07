#!/bin/sh
# Build the PLOS package: both .docx copies, the readable preview, the cover letter.
#
#   sh build.sh                      build into _stage_plos beside this script
#   PLOS_DEST=/some/dir sh build.sh  build somewhere else
#
# Nothing here writes into OneDrive. Delivery into the synced folder is a separate,
# deliberate copy step, because writing over a Files-On-Demand placeholder fails with
# 'Resource deadlock avoided' and leaves a half-written .docx in the folder a
# co-author is reading.
#
# Exits nonzero if any of the build's checks fail. A nonzero exit means do not
# deliver what is in the staging directory.
set -e
HERE=$(cd "$(dirname "$0")" && pwd)
cd "$HERE"

PY="${PYTHON:-python3}"

echo "== dependencies =="
"$PY" - <<'EOF'
import importlib, sys
missing = []
for mod, pip in (('lxml.etree', 'lxml'), ('docx', 'python-docx')):
    try:
        importlib.import_module(mod)
        print(f'  ok       {pip}')
    except Exception:
        missing.append(pip)
        print(f'  MISSING  {pip}')
print(f'  python   {sys.version.split()[0]}')
if missing:
    sys.stderr.write('\ninstall with:  python3 -m pip install ' + ' '.join(missing) + '\n')
    raise SystemExit(2)
EOF
if command -v pandoc >/dev/null 2>&1; then
  echo "  ok       pandoc"
  HAVE_PANDOC=1
else
  echo "  absent   pandoc  (the cover letter .docx will be skipped)"
  HAVE_PANDOC=0
fi

echo
echo "== manuscript =="
"$PY" -B build_plos3.py

echo
echo "== readable preview =="
"$PY" -B make_preview.py

if [ "$HAVE_PANDOC" = 1 ]; then
  echo
  echo "== cover letter =="
  if [ -f "${PLOS_DEST:-$HERE/_stage_plos}/COVER_LETTER_DRAFT.md" ]; then
    sh make_cover_letter.sh
  else
    echo "  no COVER_LETTER_DRAFT.md in the staging directory; skipped"
  fi
fi

echo
echo "== done =="
ls -l "${PLOS_DEST:-$HERE/_stage_plos}"
