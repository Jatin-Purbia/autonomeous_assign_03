"""Render the submission's Markdown report to a paginated PDF (reportlab required)."""

import json
import re
from pathlib import Path
from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    Image,
    KeepTogether,
)
from reportlab.graphics.shapes import Drawing, Rect, String

ROOT = Path(__file__).resolve().parents[1]


def chart():
    result = json.loads((ROOT / "results/experiments.json").read_text())
    drawing = Drawing(470, 185)
    for i, row in enumerate(result["summary"]):
        y = 145 - i * 29
        drawing.add(
            String(
                0,
                y + 5,
                f'p = {row["p"]}',
                fontName="Helvetica",
                fontSize=10,
                fillColor=colors.HexColor("#45534b"),
            )
        )
        drawing.add(Rect(62, y, 325, 17, fillColor=colors.HexColor("#edf1e9"), strokeColor=None))
        drawing.add(
            Rect(
                62,
                y,
                325 * row["fraction"],
                17,
                fillColor=colors.HexColor("#a5c86c"),
                strokeColor=None,
            )
        )
        drawing.add(
            String(
                402,
                y + 5,
                f'{row["fraction"]*100:.1f}%',
                fontName="Helvetica-Bold",
                fontSize=10,
                fillColor=colors.HexColor("#334c40"),
            )
        )
    return drawing


def main():
    output = ROOT / "output/pdf/assignment-03-report.pdf"
    output.parent.mkdir(parents=True, exist_ok=True)
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="BodyCustom",
            fontName="Helvetica",
            fontSize=10,
            leading=15,
            spaceAfter=9,
            textColor=colors.HexColor("#35433f"),
        )
    )
    styles.add(
        ParagraphStyle(
            name="SectionCustom",
            fontName="Helvetica-Bold",
            fontSize=15,
            leading=20,
            spaceBefore=18,
            spaceAfter=11,
            textColor=colors.HexColor("#233936"),
            keepWithNext=True,
        )
    )
    styles.add(
        ParagraphStyle(
            name="SubCustom",
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=17,
            spaceBefore=12,
            spaceAfter=8,
            textColor=colors.HexColor("#405638"),
            keepWithNext=True,
        )
    )
    styles.add(
        ParagraphStyle(
            name="SmallCustom",
            fontName="Helvetica",
            fontSize=8,
            leading=12,
            textColor=colors.HexColor("#738076"),
        )
    )
    story = []
    story.append(Spacer(1, 22 * mm))
    story.append(Paragraph("AUTONOMOUS SYSTEMS / ASSIGNMENT 03", styles["SmallCustom"]))
    story.append(Spacer(1, 9 * mm))
    story.append(
        Paragraph(
            "Argument Lab",
            ParagraphStyle(
                name="Cover",
                fontName="Helvetica-Bold",
                fontSize=36,
                leading=42,
                textColor=colors.HexColor("#233936"),
            ),
        )
    )
    story.append(Spacer(1, 4 * mm))
    story.append(
        Paragraph(
            "Abstract reasoning. Strategic reporting.<br/>Reproducible evidence.",
            ParagraphStyle(
                name="Subtitle",
                fontName="Helvetica",
                fontSize=18,
                leading=26,
                textColor=colors.HexColor("#657759"),
            ),
        )
    )
    story.append(Spacer(1, 17 * mm))
    metrics = Table(
        [
            ["5,000", "512", "3"],
            ["random instances", "exhaustive graph fixtures", "strategic agents"],
        ],
        colWidths=[55 * mm] * 3,
    )
    metrics.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 25),
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#334d3e")),
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#edf3e2")),
                ("FONTSIZE", (0, 1), (-1, 1), 9),
                ("TOPPADDING", (0, 0), (-1, -1), 14),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
            ]
        )
    )
    story.append(metrics)
    story.append(Spacer(1, 14 * mm))
    story.append(Paragraph("B.Tech project report | 8 November 2026", styles["BodyCustom"]))
    story.append(
        Paragraph(
            "Reference: Gerhard Weiss (ed.), Multiagent Systems, 2nd edition, Chapter 5.",
            styles["SmallCustom"],
        )
    )
    story.append(Spacer(1, 5 * mm))
    story.append(
        Paragraph(
            "Submission bundle: source code, README, exact textbook fixtures, test evidence, experiment data, and a recorded browser demonstration.",
            styles["BodyCustom"],
        )
    )
    story.append(PageBreak())
    text = (ROOT / "REPORT.md").read_text(encoding="utf-8")
    blocks = re.split(r"\n\s*\n", text)
    for block in blocks:
        block = block.strip()
        if not block or block.startswith("# ") or block.startswith("Autonomous Systems -"):
            continue
        if block.startswith("## "):
            story.append(Paragraph(escape(block[3:]), styles["SectionCustom"]))
            if block.startswith("## 7."):
                story.append(chart())
            continue
        if block.startswith("### "):
            story.append(Paragraph(escape(block[4:]), styles["SubCustom"]))
            continue
        if block.startswith("|"):
            rows = [
                [x.strip() for x in line.strip().strip("|").split("|")]
                for line in block.splitlines()
            ]
            rows = [r for r in rows if not all(re.fullmatch(r"[-: ]+", v) for v in r)]
            cells = [
                [
                    Paragraph(
                        escape(v),
                        ParagraphStyle(name="cell", fontSize=7.5, leading=11, fontName="Helvetica"),
                    )
                    for v in row
                ]
                for row in rows
            ]
            table = Table(cells, colWidths=[23 * mm] * len(rows[0]), repeatRows=1, hAlign="LEFT")
            table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e5edda")),
                        (
                            "ROWBACKGROUNDS",
                            (0, 1),
                            (-1, -1),
                            [colors.white, colors.HexColor("#f6f8f3")],
                        ),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("TOPPADDING", (0, 0), (-1, -1), 9),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
                        ("LINEBELOW", (0, 0), (-1, 0), 0.5, colors.HexColor("#bccbb0")),
                    ]
                )
            )
            story.append(table)
            story.append(Spacer(1, 12))
            continue
        story.append(Paragraph(escape(block.replace("\n", " ")), styles["BodyCustom"]))
    for name, title in [
        ("desktop-studio", "Framework studio - desktop"),
        ("strategic-hiding", "Profitable hiding - textbook Example 5.10"),
        ("experiments", "Experiment dashboard - submitted trials"),
    ]:
        file = ROOT / f"docs/screenshots/{name}.png"
        if file.exists():
            story.append(PageBreak())
            story.append(Paragraph(title, styles["SectionCustom"]))
            image = Image(str(file))
            scale = min((170 * mm) / image.imageWidth, (225 * mm) / image.imageHeight)
            image.drawWidth = image.imageWidth * scale
            image.drawHeight = image.imageHeight * scale
            story.append(image)
            story.append(Spacer(1, 12))
            story.append(
                Paragraph(
                    "Screenshot captured from the running application by automated browser verification.",
                    styles["SmallCustom"],
                )
            )

    def footer(canvas, doc):
        canvas.saveState()
        canvas.setStrokeColor(colors.HexColor("#dbe1d6"))
        canvas.line(20 * mm, 17 * mm, 190 * mm, 17 * mm)
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#7d897d"))
        canvas.drawString(20 * mm, 12 * mm, "ARGUMENT LAB / AUTONOMOUS SYSTEMS")
        canvas.drawRightString(190 * mm, 12 * mm, str(doc.page))
        canvas.restoreState()

    doc = SimpleDocTemplate(
        str(output),
        pagesize=(210 * mm, 297 * mm),
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=19 * mm,
        bottomMargin=23 * mm,
        title="Argument Lab - Assignment 03",
        author="Autonomous Systems project",
    )
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    print(output)


if __name__ == "__main__":
    main()
