#!/usr/bin/env bash
# Installs XeLaTeX, every package the house preamble loads, the fonts (DejaVu for symbols,
# Noto Serif Bengali for --bangla documents), and what the converter needs (pandoc, PyYAML, Pillow)
# on Debian/Ubuntu.
# Safe to re-run: it exits early when everything is already present.
set -e
need=0
for f in extarticle.cls fontspec.sty physics.sty soul.sty circuitikz.sty ltablex.sty tcolorbox.sty cleveref.sty seqsplit.sty xurl.sty wasysym.sty gensymb.sty; do
  kpsewhich "$f" >/dev/null 2>&1 || need=1
done
python3 -c "import yaml, PIL" 2>/dev/null || need=1
command -v pandoc >/dev/null || need=1
command -v xelatex >/dev/null && command -v latexmk >/dev/null && fc-list | grep -qi "DejaVu Sans" \
  && fc-list | grep -qi "Noto Serif Bengali" && [ $need = 0 ] && { echo "TeX setup OK"; exit 0; }
SUDO=""; [ "$(id -u)" = 0 ] || SUDO="sudo"
$SUDO apt-get update -q
$SUDO apt-get install -y -q --no-install-recommends texlive-xetex texlive-latex-recommended texlive-latex-extra \
  texlive-fonts-recommended texlive-pictures texlive-science texlive-plain-generic lmodern fonts-dejavu-core fonts-noto-core latexmk \
  pandoc python3-yaml python3-pil
echo "TeX setup done"
