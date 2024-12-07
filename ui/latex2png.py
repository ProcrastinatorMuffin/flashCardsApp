import os
import tempfile
from PIL import Image
import subprocess
from typing import Optional

def render_latex(latex_str: str) -> Optional[Image.Image]:
    """Render LaTeX expression to PIL Image using pdflatex"""
    
    # LaTeX document template
    doc_template = r"""
    \documentclass[12pt]{article}
    \usepackage{amsmath}
    \usepackage{amssymb}
    \pagestyle{empty}
    \begin{document}
    %s
    \end{document}
    """
    
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create LaTeX file
            tex_file = os.path.join(tmpdir, "expr.tex")
            with open(tex_file, "w") as f:
                f.write(doc_template % latex_str)
                
            # Run pdflatex
            result = subprocess.run(
                ["pdflatex", "-output-directory", tmpdir, tex_file],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True
            )
            
            # Convert PDF to PNG
            pdf_file = os.path.join(tmpdir, "expr.pdf")
            png_file = os.path.join(tmpdir, "expr.png")
            
            result = subprocess.run(
                ["convert", "-density", "300", pdf_file, "-quality", "90", png_file],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True
            )
            
            # Load and return image
            return Image.open(png_file)
    except (subprocess.CalledProcessError, OSError) as e:
        print(f"Error rendering LaTeX: {e}")
        return None

def setup_latex() -> bool:
    """Check if LaTeX is installed"""
    try:
        subprocess.run(
            ["pdflatex", "--version"], 
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True
        )
        subprocess.run(
            ["convert", "--version"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True
        )
        return True
    except subprocess.CalledProcessError:
        print("Error: pdflatex or ImageMagick not found.")
        print("Please install:")
        print("- TeX Live or MiKTeX for LaTeX support")
        print("- ImageMagick for image conversion")
        return False