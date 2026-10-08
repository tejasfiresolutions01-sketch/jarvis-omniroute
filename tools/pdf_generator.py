"""
J.A.R.V.I.S. Executive PDF Document Generator.
Converts completed autonomous task dossiers, business reports, and campaign blueprints
into professionally styled Stark Industries executive PDF documents using ReportLab.
"""

import os
import re
from datetime import datetime
from pathlib import Path
from typing import Optional, List

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.pdfgen import canvas

import config

class NumberedCanvas(canvas.Canvas):
    """Canvas that computes total page count dynamically for footers."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#555555"))

        # Header rule
        self.setStrokeColor(colors.HexColor("#007ACC"))
        self.setLineWidth(0.8)
        self.line(40, 755, 572, 755)

        # Header text
        self.drawString(40, 760, "STARK INDUSTRIES // J.A.R.V.I.S. AUTONOMOUS REPORT")
        self.drawRightString(572, 760, "CLASSIFIED // EXECUTIVE")

        # Footer rule
        self.setStrokeColor(colors.HexColor("#CCCCCC"))
        self.setLineWidth(0.5)
        self.line(40, 45, 572, 45)

        # Footer text
        self.drawString(40, 32, "VERIFIED BY J.A.R.V.I.S. BUTLER & TASK MATRIX")
        self.drawRightString(572, 32, f"Page {self._pageNumber} of {page_count}")
        self.restoreState()


class PDFGenerator:
    """Renders high-fidelity executive PDF dossiers from J.A.R.V.I.S. tasks."""

    def __init__(self, output_dir: Path = config.COMPLETED_TASKS_DIR):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        # Title style
        self._styles.add(ParagraphStyle(
            name="StarkTitle",
            fontName="Helvetica-Bold",
            fontSize=20,
            leading=24,
            textColor=colors.HexColor("#0B192C"),
            spaceAfter=6
        ))
        # Subtitle style
        self._styles.add(ParagraphStyle(
            name="StarkSubtitle",
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=14,
            textColor=colors.HexColor("#007ACC"),
            spaceAfter=12
        ))
        # H1 style
        self._styles.add(ParagraphStyle(
            name="StarkH1",
            fontName="Helvetica-Bold",
            fontSize=14,
            leading=18,
            textColor=colors.HexColor("#1E3E62"),
            spaceBefore=12,
            spaceAfter=6
        ))
        # H2 style
        self._styles.add(ParagraphStyle(
            name="StarkH2",
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=15,
            textColor=colors.HexColor("#0B192C"),
            spaceBefore=8,
            spaceAfter=4
        ))
        # Body style
        self._styles.add(ParagraphStyle(
            name="StarkBody",
            fontName="Helvetica",
            fontSize=9.5,
            leading=13.5,
            textColor=colors.HexColor("#222222"),
            spaceAfter=6
        ))
        # Bullet style
        self._styles.add(ParagraphStyle(
            name="StarkBullet",
            fontName="Helvetica",
            fontSize=9.5,
            leading=13,
            textColor=colors.HexColor("#222222"),
            leftIndent=15,
            firstLineIndent=-10,
            spaceAfter=3
        ))
        # Code/Box style
        self._styles.add(ParagraphStyle(
            name="StarkCode",
            fontName="Courier",
            fontSize=8.5,
            leading=11,
            textColor=colors.HexColor("#1A1A1A"),
            backColor=colors.HexColor("#F4F6F9"),
            borderPadding=6,
            spaceBefore=4,
            spaceAfter=6
        ))

    def _format_markdown_to_flowables(self, text: str) -> List[Any]:
        flowables = []
        lines = text.split("\n")
        in_code_block = False
        code_buffer = []

        for line in lines:
            stripped = line.strip()

            if stripped.startswith("```"):
                if in_code_block:
                    in_code_block = False
                    block_text = "<br/>".join([c.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;") for c in code_buffer])
                    flowables.append(Paragraph(block_text, self._styles["StarkCode"]))
                    flowables.append(Spacer(1, 4))
                    code_buffer = []
                else:
                    in_code_block = True
                    code_buffer = []
                continue

            if in_code_block:
                code_buffer.append(line)
                continue

            if not stripped:
                flowables.append(Spacer(1, 4))
                continue

            # Heading 1
            if stripped.startswith("# "):
                h1_text = stripped[2:].strip()
                flowables.append(Paragraph(h1_text, self._styles["StarkTitle"]))
                flowables.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#007ACC"), spaceBefore=4, spaceAfter=8))
                continue

            # Heading 2
            if stripped.startswith("## "):
                h2_text = stripped[3:].strip()
                flowables.append(Paragraph(h2_text, self._styles["StarkH1"]))
                continue

            # Heading 3
            if stripped.startswith("### "):
                h3_text = stripped[4:].strip()
                flowables.append(Paragraph(h3_text, self._styles["StarkH2"]))
                continue

            # Horizontal Rule
            if stripped in ["---", "***", "___"]:
                flowables.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#CCCCCC"), spaceBefore=6, spaceAfter=6))
                continue

            # Bullet points
            if stripped.startswith("- ") or stripped.startswith("* "):
                bullet_text = stripped[2:].strip()
                # Parse bold
                bullet_text = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", bullet_text)
                bullet_text = re.sub(r"`(.*?)`", r"<font name='Courier'>\1</font>", bullet_text)
                flowables.append(Paragraph(f"&bull; {bullet_text}", self._styles["StarkBullet"]))
                continue

            # Numbered list
            num_match = re.match(r"^(\d+)\.\s+(.*)$", stripped)
            if num_match:
                num = num_match.group(1)
                item_text = num_match.group(2)
                item_text = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", item_text)
                item_text = re.sub(r"`(.*?)`", r"<font name='Courier'>\1</font>", item_text)
                flowables.append(Paragraph(f"<b>{num}.</b> {item_text}", self._styles["StarkBullet"]))
                continue

            # Regular text
            p_text = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", stripped)
            p_text = re.sub(r"`(.*?)`", r"<font name='Courier'>\1</font>", p_text)
            flowables.append(Paragraph(p_text, self._styles["StarkBody"]))

        return flowables

    def generate_pdf(self, title: str, content: str, filename: Optional[str] = None) -> Path:
        """Renders content to an executive PDF document."""
        if not filename:
            slug = re.sub(r'[^a-zA-Z0-9_]', '_', title.lower()[:30])
            filename = f"dossier_{slug}.pdf"

        if not filename.endswith(".pdf"):
            filename += ".pdf"

        pdf_path = self.output_dir / filename

        doc = SimpleDocTemplate(
            str(pdf_path),
            pagesize=letter,
            leftMargin=40,
            rightMargin=40,
            topMargin=50,
            bottomMargin=55
        )

        story = []
        # Add metadata box
        story.append(Paragraph(title, self._styles["StarkTitle"]))
        meta_info = f"Generated by J.A.R.V.I.S. Core Matrix &bull; {datetime.now().strftime('%B %d, %Y - %I:%M %p')}"
        story.append(Paragraph(meta_info, self._styles["StarkSubtitle"]))
        story.append(Spacer(1, 6))

        # Convert and append content flowables
        flowables = self._format_markdown_to_flowables(content)
        story.extend(flowables)

        # Build document with NumberedCanvas
        doc.build(story, canvasmaker=NumberedCanvas)
        return pdf_path

    def convert_markdown_file_to_pdf(self, md_path: Path) -> Path:
        """Converts an existing .md file directly to .pdf."""
        p = Path(md_path)
        if not p.exists():
            raise FileNotFoundError(f"Markdown file {md_path} not found.")

        content = p.read_text(encoding="utf-8")
        title = p.stem.replace("_", " ").title()
        pdf_name = p.stem + ".pdf"
        return self.generate_pdf(title=title, content=content, filename=pdf_name)

# Global singleton
pdf_generator = PDFGenerator()
