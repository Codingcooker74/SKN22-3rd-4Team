from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import inch
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors
from pathlib import Path
import os
import re
from io import BytesIO


def create_pdf(markdown_text: str) -> bytes:
    """Convert Markdown text to PDF using ReportLab with table support

    Font Setup:
    1. Download NanumGothic.ttf from: https://hangeul.naver.com/font
    2. Place in: [project_root]/fonts/
    3. Restart application
    """
    # Get project root and fonts directory
    project_root = Path(__file__).parent.parent.parent
    fonts_dir = project_root / "fonts"

    # Try to find Korean font
    font_paths = [
        fonts_dir / "NanumGothic.ttf",
        fonts_dir / "MALGUN.TTF",
        fonts_dir / "malgun.ttf",
        Path("C:/Windows/Fonts/malgun.ttf"),
        Path("C:/Windows/Fonts/MALGUN.TTF"),
    ]

    korean_font = None
    for font_path in font_paths:
        if font_path.exists():
            try:
                # Register font with ReportLab
                pdfmetrics.registerFont(TTFont("KoreanFont", str(font_path)))
                korean_font = "KoreanFont"
                break
            except Exception:
                continue

    if not korean_font:
        raise RuntimeError(
            f"""한글 폰트를 찾을 수 없습니다.

PDF 생성을 위해:
1. https://hangeul.naver.com/font 에서 나눔고딕 다운로드
2. {fonts_dir} 폴더에 NanumGothic.ttf 파일 복사
3. 애플리케이션 재시작
"""
        )

    # Create PDF in memory
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # Clean markdown text
    markdown_text = re.sub(r"\[.*?버튼.*?\]", "", markdown_text)
    markdown_text = re.sub(r"\[.*?PDF.*?\]", "", markdown_text)

    # Parse and write content
    y_position = height - 1 * inch
    line_height = 14
    margin_left = 0.75 * inch
    margin_right = width - 0.75 * inch
    max_width = margin_right - margin_left

    lines = markdown_text.split("\n")
    i = 0

    while i < len(lines):
        line = lines[i].strip()

        if not line:
            y_position -= line_height / 2
            i += 1
            continue

        # Check if this is start of a table (contains | and next line is separator)
        if "|" in line and i + 1 < len(lines):
            next_line = lines[i + 1].strip()
            # Check if next line is a separator (like |---|---|)
            if re.match(r"^\|?[\s\-:|]+\|?[\s\-:|]*$", next_line):
                # Parse table
                table_data = []

                # Add header row
                header_cells = [cell.strip() for cell in line.split("|")]
                header_cells = [c for c in header_cells if c]  # Remove empty
                table_data.append(header_cells)

                # Skip separator line
                i += 2

                # Add data rows
                while i < len(lines):
                    row_line = lines[i].strip()
                    if not row_line or "|" not in row_line:
                        break
                    row_cells = [cell.strip() for cell in row_line.split("|")]
                    row_cells = [c for c in row_cells if c]  # Remove empty
                    if row_cells:
                        table_data.append(row_cells)
                    i += 1

                # Render table
                if table_data and len(table_data) > 1:
                    num_cols = len(table_data[0])
                    col_width = max_width / num_cols if num_cols > 0 else max_width

                    table = Table(table_data, colWidths=[col_width] * num_cols)
                    table.setStyle(
                        TableStyle(
                            [
                                ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                                ("FONTNAME", (0, 0), (-1, -1), korean_font),
                                ("FONTSIZE", (0, 0), (-1, -1), 8),
                                ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
                                ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                                ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                            ]
                        )
                    )

                    table_width, table_height = table.wrap(max_width, height)

                    if y_position - table_height < 1 * inch:
                        c.showPage()
                        y_position = height - 1 * inch

                    table.drawOn(c, margin_left, y_position - table_height)
                    y_position -= table_height + line_height

                continue

        # Regular text processing
        text = line
        text = re.sub(r"^#{1,6}\s+", "", text)
        text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
        text = re.sub(r"\*(.+?)\*", r"\1", text)
        text = re.sub(r"__(.+?)__", r"\1", text)
        text = re.sub(r"_(.+?)_", r"\1", text)
        text = re.sub(r"`(.+?)`", r"\1", text)
        text = re.sub(r"\[(.+?)\]\(.+?\)", r"\1", text)

        # Determine font size
        if line.startswith("#### "):
            font_size = 11
        elif line.startswith("### "):
            font_size = 13
        elif line.startswith("## "):
            font_size = 15
        elif line.startswith("# "):
            font_size = 18
        else:
            font_size = 10

        c.setFont(korean_font, font_size)
        text_width = c.stringWidth(text, korean_font, font_size)

        if text_width > max_width:
            # Word wrap
            words = text.split()
            current_line = ""

            for word in words:
                test_line = current_line + " " + word if current_line else word
                test_width = c.stringWidth(test_line, korean_font, font_size)

                if test_width > max_width and current_line:
                    if y_position < 1 * inch:
                        c.showPage()
                        c.setFont(korean_font, font_size)
                        y_position = height - 1 * inch

                    c.drawString(margin_left, y_position, current_line)
                    y_position -= line_height
                    current_line = word
                else:
                    current_line = test_line

            if current_line:
                if y_position < 1 * inch:
                    c.showPage()
                    c.setFont(korean_font, font_size)
                    y_position = height - 1 * inch

                c.drawString(margin_left, y_position, current_line)
                y_position -= line_height
        else:
            if y_position < 1 * inch:
                c.showPage()
                c.setFont(korean_font, font_size)
                y_position = height - 1 * inch

            c.drawString(margin_left, y_position, text)
            y_position -= line_height + (font_size - 10) * 0.5

        i += 1

    c.save()
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
