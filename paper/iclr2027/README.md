# ICLR 2027 Submission Package

## Title
Measuring the Value of Cognitive Sequences in LLM Research Agents

## Contents
- `main.tex` — Main paper (9 pages main text + appendix)
- `references.bib` — Bibliography
- `figures/` — Publication-quality figures (PDF + PNG)
- `tables/` — (Tables embedded in main.tex)
- `generate_figures.py` — Reproducible figure generation script

## Compilation
Requires the ICLR 2025 style file (`iclr2025_conference.sty`) as a placeholder
until the official ICLR 2027 template is released.

```bash
pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex
```

## Double-blind
This submission is anonymous. No author names, repository URLs, or identifying
information appear in the PDF.

## Checklist
- [ ] Replace iclr2025 style with official iclr2027 template when released
- [ ] Finalize author list before abstract deadline (Sep 11, 2026 AOE)
- [ ] Final page count verification (max 9 pages main text)
- [ ] Anonymous metadata check on compiled PDF
