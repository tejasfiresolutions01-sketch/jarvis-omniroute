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

    def generate_quotation_pdf(self, quote_data: dict, filename: Optional[str] = None) -> Path:
        """Renders an executive, publication-grade commercial quotation PDF."""
        quote_id = quote_data.get("quote_id", "TFS-QUOTE")
        if not filename:
            filename = f"quotation_{quote_id}.pdf"
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
        # Header / Title
        story.append(Paragraph("TEJAS FIRE SOLUTIONS // STARK DEFENSE", self._styles["StarkTitle"]))
        sub_text = f"Official Commercial Quotation &bull; Ref: <b>{quote_id}</b> &bull; Date: {quote_data.get('date', datetime.now().strftime('%Y-%m-%d'))}"
        story.append(Paragraph(sub_text, self._styles["StarkSubtitle"]))
        story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#007ACC"), spaceBefore=2, spaceAfter=8))

        # Client & Project Metadata Box
        client_name = quote_data.get("client_name", "Valued Enterprise Client")
        location = quote_data.get("facility_location", "Chennai Industrial Corridor")
        validity = quote_data.get("validity_days", 30)

        meta_table_data = [
            [
                Paragraph(f"<b>CLIENT:</b> {client_name}<br/><b>FACILITY:</b> {location}", self._styles["StarkBody"]),
                Paragraph(f"<b>VALIDITY:</b> {validity} Days<br/><b>COMPLIANCE:</b> IS 2190:2010 Standards", self._styles["StarkBody"])
            ]
        ]
        meta_table = Table(meta_table_data, colWidths=[266, 266])
        meta_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F4F6F9")),
            ('BOX', (0, 0), (-1, -1), 0.8, colors.HexColor("#D0D7DE")),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(meta_table)
        story.append(Spacer(1, 10))

        # Line Items Table
        story.append(Paragraph("<b>SCHEDULE OF SERVICES & FIRE PROTECTION HARDWARE:</b>", self._styles["StarkH2"]))
        story.append(Spacer(1, 4))

        headers = ["Item / Description", "Qty", "Rate (INR)", "Amount (INR)"]
        table_rows = [headers]

        for it in quote_data.get("items", []):
            desc = it.get("desc", it.get("description", "Service Item"))
            qty = str(it.get("qty", it.get("quantity", 1)))
            rate = f"{float(it.get('rate', it.get('unit_rate', 0.0))):,.2f}"
            amt = f"{float(it.get('amount', it.get('total', 0.0))):,.2f}"
            table_rows.append([Paragraph(desc, self._styles["StarkBody"]), qty, rate, amt])

        # Summary Rows
        subtotal = float(quote_data.get("subtotal", 0.0))
        discount_amt = float(quote_data.get("discount_amt", 0.0))
        taxable = float(quote_data.get("taxable_amount", subtotal - discount_amt))
        gst_amt = float(quote_data.get("gst_amount", 0.0))
        grand_total = float(quote_data.get("grand_total", taxable + gst_amt))

        table_rows.append(["Subtotal", "", "", f"{subtotal:,.2f}"])
        if discount_amt > 0:
            table_rows.append(["Corporate Discount", "", "", f"- {discount_amt:,.2f}"])
        table_rows.append(["Taxable Value", "", "", f"{taxable:,.2f}"])
        table_rows.append(["GST (CGST 9% + SGST 9% / 18%)", "", "", f"{gst_amt:,.2f}"])
        table_rows.append(["GRAND TOTAL (INR)", "", "", f"INR {grand_total:,.2f}"])

        item_table = Table(table_rows, colWidths=[280, 50, 92, 110])
        ts = [
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0B192C")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#D0D7DE")),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor("#EBF3FA")),
            ('TEXTCOLOR', (0, -1), (-1, -1), colors.HexColor("#0B192C")),
        ]
        item_table.setStyle(TableStyle(ts))
        story.append(item_table)
        story.append(Spacer(1, 10))

        # Terms and Compliance
        story.append(Paragraph("<b>COMPLIANCE DECLARATION & TERMS OF SERVICE:</b>", self._styles["StarkH2"]))
        terms = [
            f"&bull; <b>Standards:</b> {quote_data.get('compliance_standards', 'IS 2190:2010 Code of Practice for Selection, Installation & Maintenance.')}",
            f"&bull; <b>Certification:</b> OEM Hydrostatic proof pressure test certificates and PESO approval stickers included.",
            f"&bull; <b>Payment Terms:</b> {quote_data.get('payment_terms', '30 Days net from delivery of serviced units.')}",
            f"&bull; <b>Warranty:</b> {quote_data.get('warranty', '12 Months comprehensive warranty on refilled agents and spare parts.')}"
        ]
        for term in terms:
            story.append(Paragraph(term, self._styles["StarkBody"]))

        story.append(Spacer(1, 8))
        story.append(Paragraph("<b>Authorized Signature:</b> Tejas Fire Solutions Technical Operations Directorate &bull; J.A.R.V.I.S. Autonomous Matrix", self._styles["StarkSubtitle"]))

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

