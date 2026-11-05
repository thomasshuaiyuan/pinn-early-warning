"""Produce the PLOS Computational Biology figure set from the v10 sources.

Run: python3 make_plos_figures.py <outdir>

Writes Fig1.tif .. Fig4.tif and S1_Fig.tif (see the note on numbering below) to
<outdir>, each meeting the journal's stated figure specification: TIFF with LZW
compression, single layer, no alpha channel, RGB 8-bit, 300-600 dpi, inside
19.05 x 22.23 cm, under 10 MB. Every constraint is asserted, and the script
exits nonzero if any figure misses one.

WHY THE SOURCES ARE WHAT THEY ARE. The figure files in the repository root are
from 23 August 2026 and are stale: fig2_signal_amplitude is the superseded v9
figure, correctly archived under 4_arc/superseded_figures_v9. Do not use them.

  Fig 1  R(t) trajectories          image1.png embedded in the v10 figures docx
  Fig 2  admissions vs positivity   image4.png embedded in the v10 figures docx
  Fig 3  signal-to-noise vs lead    _figcheck_oct26/fig2_snr_within_pathogen.pdf
  Fig 4  pre-onset amplification    image3.png embedded in the v10 figures docx
  S1 Fig weekly SI discretisation   _figcheck_oct26/figS5_si_discretisation.pdf

Fig 3 and the supporting figure are rasterised from the 26 October vector PDFs
because those carry the exact permutation p-values (0.89 and 0.52) rather than
the Monte Carlo ones in the 15 October build. The other three are taken from the
images actually embedded in 2026-10-15_early-warning_v10_figures.docx, whose byte
sizes match the shipped file.

NUMBERING. The manuscript renumbered figures on 5 November so that first
citations run in ascending order: old Fig 4 -> Fig 2, old Fig 2 -> Fig 3, old
Fig 3 -> Fig 4. That permutation is already applied in the mapping above, so
this script writes the post-renumbering names directly.

The supporting figure is written as S1_Fig.tif, not S5_Fig.tif: PLOS numbers
supporting items within each type, and it is the only supporting figure. If that
reading is reversed, change SUPP_NAME below.

REPRODUCIBILITY, measured rather than assumed. Re-running this script on
5 November 2026 reproduced the delivered Fig1.tif, Fig2.tif and Fig4.tif
BYTE-IDENTICALLY: those three come from PNGs embedded in the docx, so no
rasteriser is involved. Fig3.tif and the supporting figure differ from the
delivered copies by 10 pixels of 10,089,014 and 370 of 8,241,168 respectively,
maximum channel delta 10 out of 255 — the same content at the same size and dpi,
differing only because they are rasterised from vector PDFs and the delivered
copies were produced by a different poppler build. Pixel-exact reproduction of
those two therefore requires naming the rasteriser; this run used
pdftoppm (poppler) 22.02.0 and Pillow 12.3.0. Content reproduction does not.

NOT IMPLEMENTED, and tracked as [TY-6]. PLOS states that a figure file must not
contain the figure title or caption, and three of these embed titles that
duplicate caption material; Fig 1 and Fig 3 also have unlabelled panels.
Removing them means regenerating from generate_figures.py and make_v10_figs.py
and re-checking every plotted value against its caption, which is a separate job
from this format conversion.
"""
import math, os, subprocess, sys, tempfile, zipfile

from PIL import Image

HOME = os.path.expanduser('~')
REPO = os.path.dirname(os.path.abspath(__file__))


def first_existing(label, *candidates):
    for c in candidates:
        if os.path.exists(c):
            return c
    raise SystemExit(f'{label}: none of these paths exists:\n  ' +
                     '\n  '.join(candidates))


# HKU-influenza sits at ~/Downloads on the Mac and at ~/mnt when the repository
# is reached through a mounted copy, so both are tried rather than assumed.
FIGDOCX = first_existing(
    'v10 figures docx',
    os.path.join(REPO, 'Claude outputs', '2026-10-15_early-warning_v10_figures.docx'),
    os.path.join(HOME, 'Claude outputs', '2026-10-15_early-warning_v10_figures.docx'))
FIGCHECK = first_existing(
    '_figcheck_oct26',
    os.path.join(HOME, 'Downloads', 'HKU-influenza', 'manuscript', '_figcheck_oct26'),
    os.path.join(HOME, 'mnt', 'HKU-influenza', 'manuscript', '_figcheck_oct26'),
    os.path.join(os.path.dirname(REPO), 'HKU-influenza', 'manuscript', '_figcheck_oct26'))
SUPP_NAME = 'S1_Fig.tif'

MAXW_CM, MAXH_CM, MINW_CM = 19.05, 22.23, 6.68   # the journal's page box
DPI_LO, DPI_HI = 300, 600

# target name -> ('docx', member) or ('pdf', path)
SOURCES = [
    ('Fig1.tif',  ('docx', 'word/media/image1.png')),
    ('Fig2.tif',  ('docx', 'word/media/image4.png')),
    ('Fig3.tif',  ('pdf',  os.path.join(FIGCHECK, 'fig2_snr_within_pathogen.pdf'))),
    ('Fig4.tif',  ('docx', 'word/media/image3.png')),
    (SUPP_NAME,   ('pdf',  os.path.join(FIGCHECK, 'figS5_si_discretisation.pdf'))),
]


def load(kind, ref, scratch):
    if kind == 'docx':
        with zipfile.ZipFile(FIGDOCX) as z:
            raw = z.read(ref)
        p = os.path.join(scratch, os.path.basename(ref))
        with open(p, 'wb') as fh:
            fh.write(raw)
        return Image.open(p)
    stem = os.path.join(scratch, os.path.basename(ref)[:-4])
    # vector source: rasterise generously, the dpi tag is chosen below
    subprocess.run(['pdftoppm', '-r', '600', '-png', '-singlefile', ref, stem],
                   check=True)
    return Image.open(stem + '.png')


def flatten(im):
    if im.mode in ('RGBA', 'LA', 'P'):
        bg = Image.new('RGB', im.size, (255, 255, 255))
        im = im.convert('RGBA')
        bg.paste(im, mask=im.split()[-1])
        return bg
    return im.convert('RGB')


def main(outdir):
    os.makedirs(outdir, exist_ok=True)
    rows, bad = [], []
    with tempfile.TemporaryDirectory() as scratch:
        for name, (kind, ref) in SOURCES:
            im = flatten(load(kind, ref, scratch))
            w, h = im.size
            # smallest dpi in range that keeps the figure inside the page box
            dpi = math.ceil(max(float(DPI_LO), w / (MAXW_CM / 2.54),
                                h / (MAXH_CM / 2.54)))
            if dpi > DPI_HI:                     # too many pixels for the page
                scale = DPI_HI / dpi
                im = im.resize((round(w * scale), round(h * scale)),
                               Image.LANCZOS)
                w, h = im.size
                dpi = DPI_HI
            if w / dpi * 2.54 < MINW_CM:         # too narrow at this dpi
                dpi = math.floor(w / (MINW_CM / 2.54))
            out = os.path.join(outdir, name)
            im.save(out, format='TIFF', compression='tiff_lzw', dpi=(dpi, dpi))

            chk = Image.open(out)
            mb = os.path.getsize(out) / 1e6
            wcm, hcm = w / dpi * 2.54, h / dpi * 2.54
            fails = []
            if chk.mode != 'RGB':
                fails.append('mode ' + chk.mode)
            if chk.info.get('compression') != 'tiff_lzw':
                fails.append('compression ' + str(chk.info.get('compression')))
            if getattr(chk, 'n_frames', 1) != 1:
                fails.append('multi-page')
            if mb >= 10:
                fails.append(f'{mb:.1f} MB')
            if not (MINW_CM - 1e-6 <= wcm <= MAXW_CM + 1e-6):
                fails.append(f'width {wcm:.2f} cm')
            if hcm > MAXH_CM + 1e-6:
                fails.append(f'height {hcm:.2f} cm')
            if not (DPI_LO <= dpi <= DPI_HI):
                fails.append(f'dpi {dpi}')
            rows.append((name, f'{w}x{h}', dpi, f'{wcm:.2f} x {hcm:.2f} cm',
                         f'{mb:.2f}', 'PASS' if not fails else '; '.join(fails)))
            if fails:
                bad.append(name)

    print(f'{"file":<12}{"pixels":<14}{"dpi":<6}{"on the page":<18}{"MB":<7}check')
    for r in rows:
        print(f'{r[0]:<12}{r[1]:<14}{r[2]:<6}{r[3]:<18}{r[4]:<7}{r[5]}')
    if bad:
        print('\nFAILED: ' + ', '.join(bad))
        return 1
    print('\nall figures meet the PLOS specification')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else '.'))
