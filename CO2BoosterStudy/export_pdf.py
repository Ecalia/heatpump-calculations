#!/usr/bin/env python3
"""Export CO2_Booster_Report_CF.ipynb to PDF without code cells.

Post-processes the LaTeX to:
  - Use narrower margins (more room for figures & tables)
  - Scale figures to full linewidth
  - Use smaller font in tables to prevent overflow
  - A4 paper
"""
import subprocess
import sys
import re
from pathlib import Path

NOTEBOOK = "CO2_Booster_Report_CF.ipynb"
TEX_FILE = "CO2_Booster_Report_CF.tex"
PDF_FILE = "CO2_Booster_Report_CF.pdf"
VENV_PYTHON = str(Path(__file__).parent / ".venv" / "Scripts" / "python.exe")


def export_to_latex():
    """Step 1: nbconvert → .tex (execute + no input cells)."""
    cmd = [
        VENV_PYTHON, "-m", "jupyter", "nbconvert",
        "--to", "latex", "--no-input", "--execute",
        "--ExecutePreprocessor.timeout=600",
        "--output", TEX_FILE,
        NOTEBOOK,
    ]
    print(f"[1/3] Executing notebook & exporting to LaTeX …")
    subprocess.run(cmd, check=True)


def postprocess_tex():
    """Step 2: Fix margins, figure size, table font."""
    print(f"[2/3] Post-processing {TEX_FILE} …")
    tex = Path(TEX_FILE).read_text(encoding="utf-8")

    # --- Margins: 1 in → 0.5 cm (tighter for larger graphics) -------------
    tex = tex.replace(
        r"\geometry{verbose,tmargin=1in,bmargin=1in,lmargin=1in,rmargin=1in}",
        r"\geometry{verbose,a4paper,tmargin=2cm,bmargin=2cm,lmargin=2cm,rmargin=2cm}",
    )

    # --- German locale for date (\today) and hyphenation -------------------
    # Insert babel + font setup right after \usepackage{fontspec}
    tex = tex.replace(
        r"\usepackage{fontspec}",
        r"\usepackage{fontspec}" "\n"
        r"\usepackage[ngerman]{babel}" "\n"
        r"\setmainfont{TeX Gyre Heros}"  "\n"     # neutral sans-serif (Helvetica)
        r"\setsansfont{TeX Gyre Heros}" "\n"
        r"\setmonofont{TeX Gyre Cursor}",          # monospace companion
    )

    # --- Disable automatic section numbering (we use our own 1. 2. 3.) ----
    # Also: prevent orphaned headings (heading + 1 line at page bottom)
    tex = tex.replace(
        r"\begin{document}",
        r"\setcounter{secnumdepth}{-2}" "\n"
        # Prevent page break right after a heading (keep ≥4 lines together)
        r"\usepackage{needspace}" "\n"
        r"\usepackage{titlesec}" "\n"
        r"\titleformat{\section}{\needspace{8\baselineskip}\normalfont\Large\bfseries}{\thesection}{1em}{}" "\n"
        r"\titleformat{\subsection}{\needspace{6\baselineskip}\normalfont\large\bfseries}{\thesubsection}{1em}{}" "\n"
        r"\widowpenalty=10000" "\n"
        r"\clubpenalty=10000" "\n"
        r"\begin{document}",
    )

    # --- Replace Unicode subscript ₂ with LaTeX \textsubscript{2} ----------
    # TeX Gyre Heros does not contain the ₂ glyph → use LaTeX command instead
    tex = tex.replace("₂", r"\textsubscript{2}")

    # --- Fix document title (no underscores) --------------------------------
    tex = re.sub(
        r"\\title\{[^}]*\}",
        r"\\title{CO\\textsubscript{2}-Booster-Kälteanlage --- Expander-Potentialanalyse}",
        tex,
    )

    # --- Figures: 0.9 → 1.0 linewidth ------------------------------------
    tex = tex.replace(
        r"\adjustboxset{max size={0.9\linewidth}{0.9\paperheight}}",
        r"\adjustboxset{max size={1.0\linewidth}{0.9\paperheight}}",
    )

    # --- Tables: prepend \small before every longtable --------------------
    # This makes all longtable environments use a smaller font, avoiding overflow
    tex = tex.replace(
        r"\begin{longtable}",
        r"{\small" "\n" r"\begin{longtable}",
    )
    tex = tex.replace(
        r"\end{longtable}",
        r"\end{longtable}" "\n" r"}",
    )

    # --- Ensure proper UTF-8 declaration for xelatex ---------------------
    # Already using fontspec + unicode-math via the xelatex path, so OK.

    Path(TEX_FILE).write_text(tex, encoding="utf-8")
    print(f"   ✓ Margins → 1.5 cm, figures → full width, tables → \\small, German locale")


def build_pdf():
    """Step 3: Run xelatex to build PDF."""
    print(f"[3/3] Building PDF with xelatex …")
    for i in range(2):
        result = subprocess.run(
            ["xelatex", "-interaction=nonstopmode", TEX_FILE],
            capture_output=True, text=True,
        )
        if result.returncode != 0 and i == 1:
            print("   ⚠ xelatex warnings (may be non-fatal):")
            # Show last 20 lines of log
            for line in result.stdout.splitlines()[-20:]:
                print(f"     {line}")

    if Path(PDF_FILE).exists():
        size_kb = Path(PDF_FILE).stat().st_size / 1024
        print(f"   ✓ {PDF_FILE} ({size_kb:.0f} KB)")
    else:
        print(f"   ✗ PDF not created — check {TEX_FILE.replace('.tex', '.log')}")
        sys.exit(1)


def cleanup():
    """Remove temporary LaTeX build files."""
    for ext in [".tex", ".aux", ".log", ".out"]:
        p = Path(TEX_FILE).with_suffix(ext)
        if p.exists():
            p.unlink()
    # Remove support files directory
    files_dir = Path(TEX_FILE.replace(".tex", "_files"))
    if files_dir.exists():
        import shutil
        shutil.rmtree(files_dir)


if __name__ == "__main__":
    export_to_latex()
    postprocess_tex()
    build_pdf()
    cleanup()
    print(f"\nDone → {PDF_FILE}")
