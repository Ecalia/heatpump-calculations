````skill
---
name: eng_003_jupyter_pdf_export
description: Use when exporting Jupyter notebooks (.ipynb) to professional PDF reports without code cells. Covers the full pipeline — nbconvert to LaTeX, Pandoc pitfalls (math, tables, HTML), tex post-processing (margins, fonts, section numbering, title), xelatex compilation, and cleanup. Trigger signals — "PDF export", "notebook to PDF", "report generation", "nbconvert", "LaTeX export", "xelatex", "Pandoc math". Do NOT use for HTML-only exports, Quarto workflows, or general LaTeX authoring unrelated to Jupyter.
---

# Purpose

Export a Jupyter notebook to a polished PDF report (no code cells) via nbconvert → LaTeX post-processing → xelatex, avoiding the dozen+ pitfalls that cause broken math, ugly tables, missing symbols, or compilation failures.

# Prerequisites

- Python venv with `jupyter`, `nbconvert>=7.0`, `tabulate` (for `to_markdown()`)
- Pandoc ≥ 3.x (installed system-wide or via conda)
- xelatex (MiKTeX or TeX Live) with `fontspec`, `babel`, `geometry`, `longtable` packages
- Target fonts installed: `TeX Gyre Heros` (sans-serif) + `TeX Gyre Cursor` (monospace) — or substitute

# Concrete Facts & Parameters

## Pipeline Overview

```
Step 1: jupyter nbconvert --to latex --no-input --execute notebook.ipynb
Step 2: Python post-processing of .tex file (string replacements + regex)
Step 3: xelatex -interaction=nonstopmode notebook.tex  (run TWICE for TOC/refs)
Step 4: Cleanup (.aux, .log, .out, .tex, _files/)
```

`--execute` re-runs all cells at export time → outputs are always fresh, no stale cache.  
`--no-input` hides code cells in the export.

## Pandoc Math Compatibility (CRITICAL)

nbconvert uses Pandoc internally to convert Markdown cells to LaTeX. Pandoc's Markdown math parser is stricter than Jupyter's MathJax:

### What FAILS in Pandoc

| Pattern | Problem | Fix |
|---------|---------|-----|
| `$p_0$` | Bare single letter + subscript → Pandoc may parse `_` as emphasis | `$\mathit{p}_0$` |
| `$η_s$` | Unicode Greek letter η → not in Pandoc's math font | `$\eta_\mathrm{s}$` |
| `$COP_{BITZER}$` | Multi-letter variable without wrapper | `$\mathrm{COP}_\mathrm{BITZER}$` |
| `$T_{gc,out}$` | Comma in subscript can break | `$\mathit{T}_\mathrm{gc,out}$` |
| `$\lg p$` | `\lg` renders as italic "lg" — visually confusing | `$\log(p)$` |

### Pandoc-Safe Math Patterns (ALWAYS USE THESE)

```latex
$\eta_\mathrm{s}$                          % Greek + subscript
$\mathit{p}_\mathrm{med}$                  % italic variable + subscript
$\mathrm{COP}_\mathrm{BITZER}$             % upright abbreviation
$\dot{Q}_0 \approx 98\,\mathrm{kW}$        % dot-accent + units
$\log(p)$-$h$                              % log(p)-h diagram notation
```

**Rule of thumb:** Wrap every single letter in `\mathit{}`, every abbreviation/unit in `\mathrm{}`. Never leave bare letters with `_` in Pandoc-processed Markdown cells.

## Table Rendering

### Styler Tables → Broken in PDF

`pandas.io.formats.style.Styler` objects produce HTML only. In the LaTeX export pipeline they render as `<IPython.core.display.Styler object>` or blank.

**Solution:** Convert ALL display tables to Markdown:

```python
from IPython.display import display, Markdown
display(Markdown("**Table Title**\n\n" + df.to_markdown(index=False)))
```

Requires `tabulate` package (`pip install tabulate`).

nbconvert converts Markdown tables to `longtable` environments in LaTeX → proper page breaks and formatting.

### Table Width Overflow

Wide tables overflow A4 page margins. Fix in post-processing:

```python
tex = tex.replace(r"\begin{longtable}", r"{\small" + "\n" + r"\begin{longtable}")
tex = tex.replace(r"\end{longtable}", r"\end{longtable}" + "\n" + r"}")
```

Also shorten column names in notebook code (e.g., "Übergangsjahreszeit" → "Übergang", "WRG-Modus" → "WRG").

## HTML Display Objects

`display(HTML(...))` in code cells produces a `text/plain` fallback in LaTeX export → visible as `<IPython.core.display.HTML object>`.

**Solution:** Use `publish_display_data` for HTML-only output (e.g., CSS injection):

```python
from IPython.display import publish_display_data
publish_display_data({"text/html": "<style>...</style>"})
```

This emits ONLY `text/html` MIME type — LaTeX exporter ignores it (no broken fallback).

## LaTeX Post-Processing Reference

### Margins

```python
tex = tex.replace(
    r"\geometry{verbose,tmargin=1in,bmargin=1in,lmargin=1in,rmargin=1in}",
    r"\geometry{verbose,a4paper,tmargin=1.5cm,bmargin=1.5cm,lmargin=0.5cm,rmargin=0.5cm}",
)
```

0.5 cm L/R gives maximum figure/table width. Increase to 1.5 cm if binding margin needed.

### Font (Sans-Serif)

Insert after `\usepackage{fontspec}`:

```latex
\usepackage[ngerman]{babel}       % German dates, hyphenation
\setmainfont{TeX Gyre Heros}      % Helvetica clone (sans-serif)
\setsansfont{TeX Gyre Heros}
\setmonofont{TeX Gyre Cursor}     % monospace companion
```

`babel` with `ngerman` makes `\today` emit "10. März 2026" instead of "March 10, 2026".

### Disable Section Auto-Numbering

If Markdown uses manual numbering ("1. Zusammenfassung", "2. Ergebnisse"), LaTeX auto-numbering creates double numbers ("1 1. Zusammenfassung").

```python
tex = tex.replace(r"\begin{document}", r"\setcounter{secnumdepth}{-2}" + "\n" + r"\begin{document}")
```

### Fix Document Title

nbconvert uses the filename as title (with escaped underscores). Fix via regex:

```python
import re
tex = re.sub(r"\\title\{[^}]*\}", r"\\title{Your Actual Title}", tex)
```

### Figure Width

```python
tex = tex.replace(
    r"\adjustboxset{max size={0.9\linewidth}{0.9\paperheight}}",
    r"\adjustboxset{max size={1.0\linewidth}{0.9\paperheight}}",
)
```

## Matplotlib Font Sizes for PDF

Screen-optimized font sizes (10–12 pt) are too small in PDF at 150 dpi. Double all sizes:

```python
plt.rcParams.update({
    'figure.dpi': 150, 'savefig.dpi': 150,
    'font.size': 18, 'axes.titlesize': 20, 'axes.labelsize': 18,
    'xtick.labelsize': 16, 'ytick.labelsize': 16, 'legend.fontsize': 14,
})
```

Also double any explicit `fontsize=` arguments in annotation/text calls.

# Procedure

## Step 1: Prepare Notebook for Export

1. Replace ALL `Styler` tables with `display(Markdown(df.to_markdown(index=False)))`.
2. Replace `display(HTML(...))` with `publish_display_data({"text/html": ...})`.
3. Ensure ALL Markdown math uses Pandoc-safe patterns (`\mathit{}`, `\mathrm{}`).
4. Set matplotlib rcParams for PDF-appropriate font sizes (≥16 pt).
5. Shorten table column names to prevent overflow.

**CHECK:** Run notebook in Jupyter — all cells execute without error? All tables show as Markdown? No bare `$p_0$` patterns in Markdown cells?

## Step 2: Create Export Script

Write `export_pdf.py` with 4 functions: `export_to_latex()`, `postprocess_tex()`, `build_pdf()`, `cleanup()`. Use the post-processing patterns from Concrete Facts above.

**CHECK:** Script runs without error? `.tex` file is generated?

## Step 3: Post-Process and Compile

Run the script. xelatex runs TWICE (for TOC/cross-references). Non-zero exit codes from xelatex are often non-fatal warnings — check if PDF was actually created.

**CHECK:** PDF exists and opens? Page count correct? All figures present? Math symbols render correctly? Tables fit within margins?

## Step 4: Iterate on Visual Issues

Common iteration cycle: open PDF → spot issue → fix in notebook OR post-processing → re-export. Typical issues on first export:
- Math symbols render as `?` or `□` → Pandoc-safe math patterns
- Tables overflow → shorten columns, add `\small`
- Fonts look wrong → add font configuration to post-processing
- Section numbers doubled → disable `secnumdepth`
- Title contains underscores → regex title fix
- Plot text too small → increase matplotlib font sizes

# When to Think More Abstractly

IF the notebook uses widgets, interactive plots, or Plotly → these cannot be exported to LaTeX. Consider screenshot-based workflows or switch to static matplotlib.

IF the target format is HTML (not PDF) → skip LaTeX entirely; use `nbconvert --to html --no-input --execute`. Styler tables work fine in HTML.

IF using Quarto instead of nbconvert → different pipeline, different pitfalls. This Skill does not apply.

# Common Failure Modes & Solutions

## Problem: η renders as □ or ￿
**Root cause:** Unicode Greek η in Markdown source + Pandoc cannot map it to LaTeX math.
**Solution:** Replace `η` with `$\eta$` or `$\eta_\mathrm{s}$` in Markdown cells. Never use bare Unicode Greek in math contexts.

## Problem: `<IPython.core.display.HTML object>` in PDF
**Root cause:** `display(HTML(...))` emits `text/plain` fallback that LaTeX exporter picks up.
**Solution:** Use `publish_display_data({"text/html": css_string})` — no plain-text fallback.

## Problem: `<IPython.core.display.Styler object>` in PDF
**Root cause:** Styler is HTML-only; LaTeX exporter cannot render it.
**Solution:** `df.to_markdown(index=False)` wrapped in `display(Markdown(...))`.

## Problem: xelatex fails but PDF is not created
**Root cause:** Usually a missing LaTeX package or font not found.
**Solution:** Check `.log` file for `! LaTeX Error` or `! Font ... not found`. Install via MiKTeX Console or `tlmgr`.

## Problem: Stale/empty outputs in PDF
**Root cause:** nbconvert without `--execute` uses cached outputs which may be empty or outdated.
**Solution:** Always use `--execute --ExecutePreprocessor.timeout=600`.

## Problem: Double section numbering (e.g., "1 1. Zusammenfassung")
**Root cause:** Markdown has manual numbering AND LaTeX auto-numbers sections.
**Solution:** `\setcounter{secnumdepth}{-2}` before `\begin{document}`.

# Related Skills

- **eng_001_tespy_simulation:** For the simulation code that generates the notebook content
- **eng_002_co2_booster_design:** For CO2 system domain knowledge used in the report

# Skill Maintenance Notes

**Version History:**
- v1.0 (2026-03-10): Initial creation. Captured all learnings from CO2 Booster Report PDF export pipeline (nbconvert 7.17, Pandoc 3.6.4, MiKTeX xelatex, TeX Gyre Heros font).

**Known Gaps:**
- Not tested with TeX Live (only MiKTeX on Windows)
- No guidance for multi-language documents (only German via babel)
- No handling of interactive/Plotly figures
- Progressive disclosure: could split Pandoc-safe math table into reference/ if Skill grows
````
