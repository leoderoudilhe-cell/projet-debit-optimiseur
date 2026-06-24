"""PDF Document 1 — Summary sheet (1 page)."""

from collections import defaultdict
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_RIGHT

from app.models import OptimizeResult, Piece

# Brand colours
BG = colors.HexColor("#1C1E1B")
PAPER = colors.HexColor("#F5F3EE")
WOOD = colors.HexColor("#D9A066")
WOOD_DEEP = colors.HexColor("#B97F3F")
INK_DIM = colors.HexColor("#9A9C92")
BORDER = colors.HexColor("#D8D3C4")
INK = colors.HexColor("#1C1E1B")

MONO = "Courier-Bold"
SANS = "Helvetica"


def generate_recap_pdf(result: OptimizeResult, pieces: list[Piece], project_name: str, path: str):
    doc = SimpleDocTemplate(
        path,
        pagesize=A4,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
    )

    styles = {
        "title": ParagraphStyle("title", fontName=MONO, fontSize=18, textColor=INK, spaceAfter=2 * mm),
        "sub": ParagraphStyle("sub", fontName=SANS, fontSize=9, textColor=INK_DIM, spaceAfter=6 * mm),
        "stat_label": ParagraphStyle("stat_label", fontName=SANS, fontSize=8, textColor=INK_DIM),
        "stat_val": ParagraphStyle("stat_val", fontName=MONO, fontSize=20, textColor=WOOD_DEEP),
        "section": ParagraphStyle("section", fontName=MONO, fontSize=10, textColor=INK, spaceBefore=6 * mm, spaceAfter=3 * mm),
    }

    story = []

    story.append(Paragraph(project_name, styles["title"]))
    story.append(Paragraph("Fiche récapitulative — Optimiseur de débit", styles["sub"]))
    story.append(HRFlowable(width="100%", thickness=1, color=BORDER))
    story.append(Spacer(1, 6 * mm))

    # Stats row
    stats_data = [
        [
            _stat_cell(str(result.total_panels), "panneaux utilisés"),
            _stat_cell(f"{result.global_waste_ratio:.1f}%", "taux de chute"),
            _stat_cell(str(result.materials_count), "matériaux"),
            _stat_cell(str(result.total_pieces), "pièces placées"),
            _stat_cell(f"{result.consumed_area_m2:.2f} m²", "surface consommée"),
        ]
    ]
    stats_table = Table(stats_data, colWidths=["20%"] * 5)
    stats_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), PAPER),
        ("BOX", (0, 0), (-1, -1), 1, BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, BORDER),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(stats_table)
    story.append(Spacer(1, 8 * mm))

    # Panels by group
    story.append(Paragraph("Panneaux par groupe", styles["section"]))
    panel_groups: dict[tuple[int, str], int] = defaultdict(int)
    for panel in result.panels:
        panel_groups[(panel.thickness, panel.material)] += 1

    pg_data = [["Épaisseur", "Matériau", "Nb panneaux"]]
    for (thickness, material), count in sorted(panel_groups.items()):
        pg_data.append([f"{thickness} mm", material, str(count)])

    pg_table = Table(pg_data, colWidths=[30 * mm, None, 30 * mm])
    pg_table.setStyle(_table_style())
    story.append(pg_table)
    story.append(Spacer(1, 8 * mm))

    # Pieces list
    story.append(Paragraph("Liste des pièces", styles["section"]))
    p_data = [["N° LP", "Nom", "Matériau", "É.", "Larg.", "Long.", "Qté", "Fil"]]
    for piece in pieces:
        p_data.append([
            piece.lp_number,
            piece.name[:30],
            piece.material[:25],
            f"{piece.thickness}",
            f"{piece.width}",
            f"{piece.length}",
            f"{piece.quantity}",
            "✓" if piece.grain_locked else "—",
        ])

    p_table = Table(p_data, colWidths=[18 * mm, 40 * mm, 50 * mm, 12 * mm, 16 * mm, 16 * mm, 12 * mm, 12 * mm])
    p_table.setStyle(_table_style())
    story.append(p_table)

    doc.build(story)


def _stat_cell(value: str, label: str) -> Table:
    data = [[Paragraph(value, ParagraphStyle("v", fontName=MONO, fontSize=16, textColor=WOOD_DEEP, alignment=1))],
            [Paragraph(label, ParagraphStyle("l", fontName=SANS, fontSize=7, textColor=INK_DIM, alignment=1))]]
    t = Table(data)
    return t


def _table_style() -> TableStyle:
    return TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E8E4DA")),
        ("FONTNAME", (0, 0), (-1, 0), MONO),
        ("FONTSIZE", (0, 0), (-1, 0), 8),
        ("FONTNAME", (0, 1), (-1, -1), SANS),
        ("FONTSIZE", (0, 1), (-1, -1), 8),
        ("TEXTCOLOR", (0, 0), (-1, -1), INK),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [PAPER, colors.HexColor("#EDEBE5")]),
        ("BOX", (0, 0), (-1, -1), 1, BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, BORDER),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ])
