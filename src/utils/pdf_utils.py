from fpdf import FPDF
import re


class ReportPDF(FPDF):
    def header(self):
        self.set_font("helvetica", "B", 15)
        self.cell(0, 10, "Investment Analysis Report", align="C")
        self.ln(20)

    def footer(self):
        self.set_y(-15)
        self.set_font("helvetica", "I", 8)
        self.cell(0, 10, f"Page {self.page_no()}", align="C")


def create_pdf(markdown_text: str) -> bytes:
    """Convert simplistic Markdown to PDF bytes"""
    pdf = ReportPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Fonts - Using standard fonts to avoid font file dependency issues
    # Note: Default fonts don't support Korean characters well.
    # For robust Korean support, we'd need a TTF font file (e.g., NanumGothic).
    # Since we can't easily download one here, we might have issues with Korean text.
    # Fallback: We will try to use a standard font, but Korean might appear as squares if not supported.
    # Ideally, we should include a font. For now, let's assume English or standard encoding.
    # Wait, the user is Korean. This is a problem.
    # fpdf2 has basic unicode support but needs a font.
    # I will stick to English for headers but try to use a unicode font if possible.
    # Actually, without a .ttf file, Korean won't render in FPDF.

    # Strategy: Suggest installing a font or use a library that handles it.
    # Or, since I cannot upload a font file, I will just implement the structure
    # and warn about Korean font requirement.
    # BUT, I can try to use 'Arial Unicode MS' if available on system? No.
    # Reverting decision: Streamlit is running on Windows (User's PC).
    # I can try to point to a Windows font. c:/Windows/Fonts/malgun.ttf

    font_path = "c:/Windows/Fonts/malgun.ttf"
    try:
        pdf.add_font("MalgunGothic", fname=font_path)
        pdf.set_font("MalgunGothic", size=10)
    except:
        pdf.set_font("helvetica", size=10)

    # Simple Markdown Parsing (Headers, Bold)
    lines = markdown_text.split("\n")

    for line in lines:
        line = line.strip()
        if not line:
            pdf.ln(5)
            continue

        if line.startswith("# "):
            pdf.set_font(style="B", size=16)
            pdf.cell(0, 10, line[2:], ln=True)
            pdf.set_font(style="", size=10)
        elif line.startswith("## "):
            pdf.set_font(style="B", size=14)
            pdf.cell(0, 10, line[3:], ln=True)
            pdf.set_font(style="", size=10)
        elif line.startswith("### "):
            pdf.set_font(style="B", size=12)
            pdf.cell(0, 10, line[4:], ln=True)
            pdf.set_font(style="", size=10)
        elif line.startswith("- "):
            pdf.cell(5)  # Indent
            pdf.multi_cell(0, 7, f"- {line[2:]}")  # bullet
        elif line.startswith("**") and line.endswith("**"):
            pdf.set_font(style="B", size=10)
            pdf.multi_cell(0, 7, line.replace("**", ""))
            pdf.set_font(style="", size=10)
        else:
            pdf.multi_cell(0, 7, line)

    return pdf.output()
