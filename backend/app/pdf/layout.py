"""PDF Document 2 — Layout plans, one A4 page per panel.

Each plan shows:
- Placed pieces with dimensions (adaptive font, falls back to a page legend)
- Grain direction hatch on grain-locked pieces
- Horizontal CUT LINES with their Y-position and cut number (H1, H2 …)
  so Tom can program the panel saw directly from the plan

Orientation (retour atelier Tom) : on coupe à la scie à panneaux DEPUIS LE HAUT
en descendant (on enlève chaque bande coupée, sinon la chute reste au-dessus et
bloque la lame). Le plan est donc rendu « du haut vers le bas » : la 1ʳᵉ bande
empaquetée est en HAUT, la chute en BAS, et les coupes H1, H2… sont numérotées
du haut vers le bas. (Le moteur empile en interne depuis son origine ; on inverse
uniquement l'axe Y au rendu — origine moteur = haut du panneau.)
"""

from __future__ import annotations

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Spacer, PageBreak
from reportlab.platypus.flowables import Flowable
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph
from reportlab.pdfbase.pdfmetrics import stringWidth

from app.models import OptimizeResult, Panel, PlacedPiece

PAPER = colors.HexColor("#F5F3EE")
WOOD_LIGHT = colors.Color(0.851, 0.627, 0.400, alpha=0.55)
BORDER = colors.HexColor("#D8D3C4")
INK = colors.HexColor("#1C1E1B")
INK_DIM = colors.HexColor("#9A9C92")
GRAIN_HATCH = colors.HexColor("#B97F3F")
CUT_LINE = colors.HexColor("#C44536")   # red — clearly a cut instruction

MONO = "Courier-Bold"
SANS = "Helvetica"
MIN_FONT_PT = 6


def _fit_font(label: str, dims: str, w_pts: float, h_pts: float) -> float:
    """Plus grande police (≤10pt) pour laquelle n° + cotes tiennent dans le
    rectangle. Renvoie une valeur < MIN_FONT_PT si rien ne tient proprement
    (→ bascule en légende). N'utilise pas de canvas : décision reproductible
    aussi bien au pré-calcul de la légende qu'au rendu."""
    for size in [10, 8, 7, 6, MIN_FONT_PT - 0.5]:
        lw = stringWidth(label, MONO, size)
        dw = stringWidth(dims, SANS, max(size - 1.5, MIN_FONT_PT))
        if max(lw, dw) + 4 <= w_pts - 4 and size * 2.8 <= h_pts - 4:
            return size
    return MIN_FONT_PT - 0.5


def _legend_for_panel(panel: Panel, scale: float) -> dict[str, str]:
    """Pièces dont le texte ne tient pas dans le rectangle → {n° position: cotes}.
    Calculé AVANT le rendu pour que la légende de bas de page soit réellement
    remplie (le rendu du flowable, lui, ne s'exécute qu'au doc.build())."""
    legend: dict[str, str] = {}
    for pp in panel.placed:
        w_pts, h_pts = pp.w * scale, pp.h * scale
        label = str(pp.piece.lp_number)
        dims = f"{pp.w}×{pp.h}"
        if _fit_font(label, dims, w_pts, h_pts) < MIN_FONT_PT:
            legend[label] = dims
    return legend


class PanelFlowable(Flowable):
    def __init__(self, panel: Panel, scale: float, draw_w: float, draw_h: float):
        super().__init__()
        self.panel = panel
        self.scale = scale
        self.draw_w = draw_w
        self.draw_h = draw_h
        self.width = draw_w
        self.height = draw_h

    def _flip_y(self, y_mm: float, h_mm: float = 0.0) -> float:
        """Inverse l'axe Y : origine moteur (y=0) → HAUT du panneau au rendu."""
        return (self.panel.height - y_mm - h_mm) * self.scale

    def draw(self):
        c = self.canv
        s = self.scale
        panel = self.panel

        # Panel background
        c.setFillColor(PAPER)
        c.setStrokeColor(BORDER)
        c.setLineWidth(0.8)
        c.rect(0, 0, self.draw_w, self.draw_h, fill=1, stroke=1)

        # ── Placed pieces (axe Y inversé → 1ʳᵉ bande en haut) ───────────────
        for pp in panel.placed:
            x = pp.x * s
            y = self._flip_y(pp.y, pp.h)
            w = pp.w * s
            h = pp.h * s

            c.setFillColor(WOOD_LIGHT)
            c.setStrokeColor(GRAIN_HATCH)
            c.setLineWidth(0.5)
            c.rect(x, y, w, h, fill=1, stroke=1)

            if pp.piece.grain_locked:
                self._draw_grain_hatch(c, x, y, w, h)

            label = str(pp.piece.lp_number)
            dims = f"{pp.w}×{pp.h}"
            font_size = _fit_font(label, dims, w, h)

            if font_size >= MIN_FONT_PT:
                c.setFillColor(INK)
                c.setFont(MONO, font_size)
                c.drawCentredString(x + w / 2, y + h / 2 + font_size * 0.15, label)
                c.setFont(SANS, max(font_size - 1.5, MIN_FONT_PT))
                c.drawCentredString(x + w / 2, y + h / 2 - font_size * 1.2, dims)
            else:
                # Trop petit : on n'affiche que le n° ; les cotes sont en légende.
                c.setFillColor(INK)
                c.setFont(MONO, min(8, max(MIN_FONT_PT, h * 0.4)))
                c.drawCentredString(x + w / 2, y + h / 2 - 3, label)

        # ── Horizontal cut lines (depuis le haut) ───────────────────────────
        for cut_idx, cut_y_mm in enumerate(panel.shelf_cuts, start=1):
            cut_y_pts = self._flip_y(cut_y_mm)
            if cut_y_pts <= 0 or cut_y_pts >= self.draw_h:
                continue

            # Dashed red line across the full panel width
            c.saveState()
            c.setStrokeColor(CUT_LINE)
            c.setLineWidth(0.6)
            c.setDash([4, 3])
            c.line(0, cut_y_pts, self.draw_w, cut_y_pts)
            c.restoreState()

            # Cut label on the right edge: "H1 — 291mm" (distance depuis le haut)
            label = f"H{cut_idx} — {cut_y_mm}mm"
            c.setFillColor(CUT_LINE)
            c.setFont(SANS, 5.5)
            c.drawRightString(self.draw_w - 2, cut_y_pts + 1.5, label)

    def _draw_grain_hatch(self, c, x, y, w, h):
        c.saveState()
        p = c.beginPath()
        p.rect(x, y, w, h)
        c.clipPath(p, stroke=0, fill=0)
        c.setStrokeColor(colors.Color(0.725, 0.498, 0.247, alpha=0.4))
        c.setLineWidth(0.4)
        step = 6
        for i in range(int((w + h) / step) + 1):
            ox = x + i * step
            c.line(ox, y, ox - h, y + h)
        c.restoreState()


def generate_layout_pdf(result: OptimizeResult, project_name: str, path: str):
    PAGE_W, PAGE_H = A4
    margin = 15 * mm

    doc = SimpleDocTemplate(
        path,
        pagesize=A4,
        leftMargin=margin,
        rightMargin=margin,
        topMargin=margin,
        bottomMargin=margin,
    )

    header_h = 22 * mm
    legend_h = 22 * mm
    draw_area_w = PAGE_W - 2 * margin
    draw_area_h = PAGE_H - 2 * margin - header_h - legend_h

    story = []

    for i, panel in enumerate(result.panels):
        scale_x = draw_area_w / panel.width
        scale_y = draw_area_h / panel.height
        scale = min(scale_x, scale_y)

        drawn_w = panel.width * scale
        drawn_h = panel.height * scale

        # Légende calculée AVANT le rendu (correctif : sinon le dict est vide).
        legend = _legend_for_panel(panel, scale)

        has_grain = any(pp.piece.grain_locked for pp in panel.placed)
        grain_tag = " · FIL OBLIGATOIRE" if has_grain else ""
        header_text = (
            f"Panneau {i + 1}/{result.total_panels} · {panel.material} · "
            f"ép. {panel.thickness} mm · {panel.width}×{panel.height} mm"
            f"{grain_tag}  |  chute {panel.waste_ratio:.1f}%"
        )
        story.append(Paragraph(
            header_text,
            ParagraphStyle("h", fontName=MONO, fontSize=7, textColor=INK, spaceAfter=3 * mm),
        ))

        # Cut sequence legend — depuis le haut du panneau
        if panel.shelf_cuts:
            cuts_text = "Coupes horizontales (depuis le haut) : " + "  ".join(
                f"H{j+1}={y}mm" for j, y in enumerate(panel.shelf_cuts)
            )
            story.append(Paragraph(
                cuts_text,
                ParagraphStyle("cuts", fontName=SANS, fontSize=6.5,
                               textColor=CUT_LINE, spaceAfter=2 * mm),
            ))

        story.append(PanelFlowable(panel, scale, drawn_w, drawn_h))

        # Légende des pièces trop petites pour afficher leurs cotes dans le rectangle
        if legend:
            leg_text = "Légende cotes (pièces trop petites) : " + "  |  ".join(
                f"n°{k} = {v}" for k, v in legend.items()
            )
            story.append(Paragraph(
                leg_text,
                ParagraphStyle("leg", fontName=SANS, fontSize=6.5, textColor=INK_DIM,
                               spaceBefore=3 * mm),
            ))
        else:
            story.append(Spacer(1, 3 * mm))

        if i < len(result.panels) - 1:
            story.append(PageBreak())

    doc.build(story)
