import math
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import config
from config import sx, sy
from colors import *
from .tema import Tema
from .estilo_base import EstiloBase
from calendar_engine import nome_mes, nome_dia

_FONT_B = "Helvetica-Bold"
_FONT = "Helvetica"

tema = Tema(
    nome="Floral",
    primaria="#FFFFFF",
    secundaria="#FFF8FB",
    destaque="#C2185B",
    texto="#4A2C2A",
    texto_secundario="#8D6E63",
    linhas="#F3D1DC",
    bordas="#E8A0B8",
    cabecalho="#C2185B",
    texto_cabecalho="#FFFFFF",
    prioridade="#C2185B",
    mini_borda="#F3D1DC",
    mini_texto="#4A2C2A",
    mini_domingo="#C62828",
    feriado="#C62828",
    fonte_titulo="Helvetica-Bold",
    fonte_texto="Helvetica",
)

COR_STEM = HexColor("#7CB342")
COR_LEAF = HexColor("#AED581")
COR_PETAL_1 = HexColor("#F8BBD0")
COR_PETAL_2 = HexColor("#F48FB1")
COR_CENTER = HexColor("#FFD54F")
COR_VINE = HexColor("#C5E1A5")
COR_HEADER_TXT = HexColor("#FFFFFF")


def _draw_flower(pdf, cx, cy, r, petal_cor, center_cor, num_petals=5):
    pdf.setFillColor(petal_cor)
    for i in range(num_petals):
        angle = math.radians(i * (360 / num_petals))
        px = cx + r * 0.55 * math.cos(angle)
        py = cy + r * 0.55 * math.sin(angle)
        pdf.circle(px * mm, py * mm, r * 0.4 * mm, fill=1, stroke=0)
    pdf.setFillColor(center_cor)
    pdf.circle(cx * mm, cy * mm, r * 0.25 * mm, fill=1, stroke=0)


def _draw_leaf(pdf, cx, cy, size, angle_deg, cor):
    pdf.saveState()
    pdf.translate(cx * mm, cy * mm)
    pdf.rotate(angle_deg)
    pdf.setFillColor(cor)
    pdf.ellipse(0, -size * 0.2 * mm, size * mm, size * 0.2 * mm, fill=1, stroke=0)
    pdf.restoreState()


def _draw_vine_border(pdf, x, y_start, y_end, side="left"):
    pdf.setStrokeColor(COR_VINE)
    pdf.setLineWidth(0.3)
    steps = 4
    step = (y_start - y_end) / steps
    for i in range(steps):
        yy = y_start - i * step
        if side == "left":
            _draw_leaf(pdf, x + 1, yy, 2, 30 + i * 20, COR_LEAF)
        else:
            _draw_leaf(pdf, x - 1, yy, 2, 150 - i * 20, COR_LEAF)


class Floral(EstiloBase):
    nome = "Floral"

    def fundo_pagina(self, pdf):
        pdf.setFillColor(HexColor("#FFFAF5"))
        pdf.rect(0, 0, config.LARGURA, config.ALTURA, fill=1, stroke=0)

    def faixa_mes(self, pdf, x, y, w, h, data):
        accent = self._theme_accent()
        pdf.setFillColor(accent)
        pdf.roundRect(sx(x * mm), sy(y * mm), sx(w * mm), sy(h * mm), 3 * mm, fill=1, stroke=0)
        _draw_flower(pdf, x + 2.5, y + h / 2, 1.5, COR_PETAL_1, COR_CENTER)
        pdf.saveState()
        cx = sx((x + w / 2) * mm)
        cy = sy((y + h / 2) * mm)
        pdf.translate(cx, cy)
        pdf.rotate(90)
        pdf.setFont(_FONT_B, 9)
        pdf.setFillColor(COR_HEADER_TXT)
        pdf.drawCentredString(0, 0, nome_mes(data.month).upper())
        pdf.restoreState()

    def cabecalho_diario(self, pdf, data, x, y, w, h, is_2dpp=False, espelhar=False):
        accent = self._theme_accent()
        pdf.setFillColor(HexColor("#FFFAF5"))
        pdf.rect(sx(x * mm), sy(y * mm), sx(w * mm), sy(h * mm), fill=1, stroke=0)
        if is_2dpp:
            pdf.setFillColor(accent)
            pdf.roundRect(sx(x * mm), sy((y + h - 12) * mm), sx(w * mm), sy(12 * mm), 3 * mm, fill=1, stroke=0)
            pdf.rect(sx(x * mm), sy((y + h - 8) * mm), sx(w * mm), sy(8 * mm), fill=1, stroke=0)
            _draw_flower(pdf, x + w - 4, y + h - 6, 1.5, COR_PETAL_1, COR_CENTER)
            pdf.setFont(_FONT_B, 16)
            pdf.setFillColor(BRANCO)
            pdf.drawString(sx((x + 3) * mm), sy((y + h - 9) * mm), data.strftime("%d"))
            if espelhar:
                pdf.setFont(_FONT_B, 9)
                pdf.setFillColor(HexColor("#6D4C5A"))
                pdf.drawString(sx((x + 3) * mm), sy((y + 5) * mm), nome_dia(data).upper())
                pdf.setFont(_FONT, 7)
                pdf.setFillColor(HexColor("#A07D8A"))
                pdf.drawString(sx((x + 3) * mm), sy((y + 1) * mm), data.strftime("%d/%m/%Y"))
                _draw_leaf(pdf, x + w - 8, y + 4, 1.5, 200, COR_LEAF)
            else:
                pdf.setFont(_FONT_B, 9)
                pdf.setFillColor(HexColor("#6D4C5A"))
                pdf.drawRightString(sx((x + w - 3) * mm), sy((y + 6) * mm), nome_dia(data).upper())
                pdf.setFont(_FONT, 7)
                pdf.setFillColor(HexColor("#A07D8A"))
                pdf.drawRightString(sx((x + w - 3) * mm), sy((y + 1) * mm), data.strftime("%d/%m/%Y"))
                _draw_leaf(pdf, x + 10, y + 4, 1.5, 30, COR_LEAF)
        else:
            pdf.setFillColor(accent)
            pdf.roundRect(sx(x * mm), sy((y + h - 14) * mm), sx(w * mm), sy(14 * mm), 3 * mm, fill=1, stroke=0)
            pdf.rect(sx(x * mm), sy((y + h - 10) * mm), sx(w * mm), sy(10 * mm), fill=1, stroke=0)
            _draw_flower(pdf, x + w - 5, y + h - 7, 2, COR_PETAL_1, COR_CENTER)
            pdf.setFont(_FONT_B, 40)
            pdf.setFillColor(BRANCO)
            pdf.drawRightString(sx((x + w - 5) * mm), sy((y + 14) * mm), data.strftime("%d"))
            pdf.setFont(_FONT_B, 10)
            pdf.setFillColor(HexColor("#6D4C5A"))
            pdf.drawRightString(sx((x + w - 5) * mm), sy((y + 6) * mm), nome_dia(data).upper())
            pdf.setFont(_FONT, 7)
            pdf.setFillColor(HexColor("#A07D8A"))
            pdf.drawRightString(sx((x + w - 5) * mm), sy((y + 1) * mm), data.strftime("%d/%m/%Y"))
            _draw_leaf(pdf, x + 12, y + 5, 2, 30, COR_LEAF)

    def caixa_prioridades(self, pdf, x, y, w, h):
        accent = self._theme_accent()
        pdf.setFillColor(HexColor("#FFF5F8"))
        pdf.setStrokeColor(HexColor("#F3D1DC"))
        pdf.setLineWidth(0.5)
        pdf.roundRect(sx(x * mm), sy(y * mm), sx(w * mm), sy(h * mm), 3 * mm, fill=1, stroke=1)
        pdf.setFillColor(accent)
        pdf.roundRect(sx(x * mm), sy((y + h - 9) * mm), sx(w * mm), sy(9 * mm), 3 * mm, fill=1, stroke=0)
        pdf.rect(sx(x * mm), sy((y + h - 6) * mm), sx(w * mm), sy(6 * mm), fill=1, stroke=0)
        _draw_flower(pdf, x + 5, y + h - 4.5, 1.2, COR_PETAL_1, COR_CENTER)
        pdf.setFont(_FONT_B, 8)
        pdf.setFillColor(COR_HEADER_TXT)
        pdf.drawCentredString(sx((x + w / 2) * mm), sy((y + h - 6) * mm), "PRIORIDADES")
        espacamento = (h - 14) / 4
        yy = y + h - 14
        dot_colors = [accent, HexColor("#E91E63"), HexColor("#F06292"), HexColor("#F8BBD0")]
        for cor in dot_colors:
            pdf.setFillColor(cor)
            pdf.circle(sx((x + 6) * mm), sy(yy * mm), 0.8 * mm, fill=1, stroke=0)
            pdf.setStrokeColor(HexColor("#F3D1DC"))
            pdf.setLineWidth(0.2)
            pdf.line(sx((x + 9) * mm), sy(yy * mm), sx((x + w - 5) * mm), sy(yy * mm))
            yy -= espacamento

    def area_anotacoes(self, pdf, x, y, w, h, num_linhas=8):
        accent = self._theme_accent()
        pdf.setFillColor(HexColor("#FFF5F8"))
        pdf.setStrokeColor(HexColor("#F3D1DC"))
        pdf.setLineWidth(0.4)
        pdf.roundRect(sx(x * mm), sy(y * mm), sx(w * mm), sy(h * mm), 3 * mm, fill=1, stroke=1)
        pdf.setFillColor(accent)
        pdf.roundRect(sx(x * mm), sy((y + h - 8) * mm), sx(w * mm), sy(8 * mm), 3 * mm, fill=1, stroke=0)
        pdf.rect(sx(x * mm), sy((y + h - 5) * mm), sx(w * mm), sy(5 * mm), fill=1, stroke=0)
        _draw_flower(pdf, x + w / 2, y + h - 4, 1.2, COR_PETAL_1, COR_CENTER)
        pdf.setFont(_FONT_B, 7)
        pdf.setFillColor(COR_HEADER_TXT)
        pdf.drawCentredString(sx((x + w / 2) * mm), sy((y + h - 5.5) * mm), "ANOTACOES")
        espacamento = (h - 12) / (num_linhas + 1)
        yy = y + h - 12
        for i in range(num_linhas):
            pdf.setStrokeColor(HexColor("#F3D1DC"))
            pdf.setLineWidth(0.2)
            pdf.line(sx((x + 4) * mm), sy(yy * mm), sx((x + w - 4) * mm), sy(yy * mm))
            yy -= espacamento

    def divisor(self, pdf, x1, y, x2):
        mid = (x1 + x2) / 2
        pdf.setStrokeColor(HexColor("#F3D1DC"))
        pdf.setLineWidth(0.3)
        pdf.line(sx(x1 * mm), sy(y * mm), sx((mid - 2) * mm), sy(y * mm))
        pdf.line(sx((mid + 2) * mm), sy(y * mm), sx(x2 * mm), sy(y * mm))
        _draw_flower(pdf, mid, y, 1.2, COR_PETAL_1, COR_CENTER, 5)

    def decorar_canto(self, pdf, x, y, corner="tl"):
        _draw_flower(pdf, x, y, 2.5, COR_PETAL_1, COR_CENTER)
        _draw_leaf(pdf, x + 2, y - 1, 2, 30, COR_LEAF)
        _draw_leaf(pdf, x - 1, y - 2, 1.5, 280, COR_LEAF)

    def decorar_borda(self, pdf):
        pw = config.LARGURA / mm
        ph = config.ALTURA / mm
        pdf.setStrokeColor(HexColor("#F3D1DC"))
        pdf.setLineWidth(0.4)
        pdf.roundRect(sx(5 * mm), sy(5 * mm), sx((pw - 10) * mm), sy((ph - 10) * mm), 3 * mm, fill=0, stroke=1)
        _draw_vine_border(pdf, 5, ph - 10, ph / 2, "left")
        _draw_vine_border(pdf, pw - 5, ph - 10, ph / 2, "right")
        _draw_vine_border(pdf, 5, 10, ph / 2, "left")
        _draw_vine_border(pdf, pw - 5, 10, ph / 2, "right")
        _draw_flower(pdf, 8, ph - 8, 3, COR_PETAL_1, COR_CENTER)
        _draw_flower(pdf, pw - 8, ph - 8, 2.5, COR_PETAL_2, COR_CENTER)
        _draw_flower(pdf, 8, 8, 2.5, COR_PETAL_2, COR_CENTER)
        _draw_flower(pdf, pw - 8, 8, 3, COR_PETAL_1, COR_CENTER)
        _draw_leaf(pdf, 12, ph - 10, 3, 45, COR_LEAF)
        _draw_leaf(pdf, pw - 12, ph - 10, 3, 135, COR_LEAF)
        _draw_leaf(pdf, 12, 10, 3, 315, COR_LEAF)
        _draw_leaf(pdf, pw - 12, 10, 3, 225, COR_LEAF)

    def pagina_dados_pessoais(self, pdf, campos):
        self.decorar_borda(pdf)
        self.fundo_pagina(pdf)
        accent = self._theme_accent()
        pw = config.LARGURA / mm
        ph = config.ALTURA / mm
        pdf.setFillColor(accent)
        pdf.roundRect(sx(15 * mm), sy((ph - 35) * mm), sx((pw - 30) * mm), sy(18 * mm), 3 * mm, fill=1, stroke=0)
        _draw_flower(pdf, pw / 2 - 35, ph - 26, 3, COR_PETAL_1, COR_CENTER)
        _draw_flower(pdf, pw / 2 + 35, ph - 26, 2.5, COR_PETAL_2, COR_CENTER)
        _draw_leaf(pdf, pw / 2 - 32, ph - 28, 2, 45, COR_LEAF)
        _draw_leaf(pdf, pw / 2 + 32, ph - 28, 2, 135, COR_LEAF)
        pdf.setFont(_FONT_B, 18)
        pdf.setFillColor(COR_HEADER_TXT)
        pdf.drawCentredString(sx(pw / 2 * mm), sy((ph - 27) * mm), "DADOS PESSOAIS")
        yy = ph - 50
        for campo in campos:
            pdf.setFont(_FONT_B, 8)
            pdf.setFillColor(HexColor("#6D4C5A"))
            pdf.drawString(sx(20 * mm), sy(yy * mm), campo)
            pdf.setStrokeColor(HexColor("#F3D1DC"))
            pdf.setLineWidth(0.25)
            pdf.line(sx(20 * mm), sy((yy - 2) * mm), sx((pw - 20) * mm), sy((yy - 2) * mm))
            _draw_flower(pdf, 18, yy - 1, 0.5, COR_PETAL_1, COR_CENTER, 3)
            yy -= 18
        pdf.showPage()

    def planejamento(self, pdf, caixas):
        self.decorar_borda(pdf)
        self.fundo_pagina(pdf)
        accent = self._theme_accent()
        pw = config.LARGURA / mm
        ph = config.ALTURA / mm
        pdf.setFillColor(accent)
        pdf.roundRect(sx(10 * mm), sy((ph - 28) * mm), sx((pw - 20) * mm), sy(14 * mm), 3 * mm, fill=1, stroke=0)
        _draw_flower(pdf, pw / 2 - 40, ph - 21, 2.5, COR_PETAL_1, COR_CENTER)
        _draw_flower(pdf, pw / 2 + 40, ph - 21, 2, COR_PETAL_2, COR_CENTER)
        _draw_leaf(pdf, pw / 2 - 37, ph - 23, 2, 45, COR_LEAF)
        _draw_leaf(pdf, pw / 2 + 37, ph - 23, 2, 135, COR_LEAF)
        pdf.setFont(_FONT_B, 16)
        pdf.setFillColor(COR_HEADER_TXT)
        pdf.drawCentredString(sx(pw / 2 * mm), sy((ph - 22) * mm), "PLANEJAMENTO ANUAL")
        pdf.setFont(_FONT, 8)
        pdf.setFillColor(HexColor("#A07D8A"))
        pdf.drawCentredString(sx(pw / 2 * mm), sy((ph - 33) * mm), "Metas e Objetivos")
        for titulo, y, alt in caixas:
            pdf.setFillColor(HexColor("#FFF5F8"))
            pdf.setStrokeColor(HexColor("#F3D1DC"))
            pdf.setLineWidth(0.4)
            pdf.roundRect(sx(15 * mm), sy(y * mm), sx(118 * mm), sy(alt * mm), 3 * mm, fill=1, stroke=1)
            pdf.setFillColor(accent)
            pdf.roundRect(sx(15 * mm), sy((y + alt - 8) * mm), sx(118 * mm), sy(8 * mm), 3 * mm, fill=1, stroke=0)
            pdf.rect(sx(15 * mm), sy((y + alt - 5) * mm), sx(118 * mm), sy(5 * mm), fill=1, stroke=0)
            _draw_flower(pdf, 18, y + alt - 4, 1.2, COR_PETAL_1, COR_CENTER, 4)
            _draw_flower(pdf, 131, y + alt - 4, 1, COR_PETAL_2, COR_CENTER, 4)
            pdf.setFont(_FONT_B, 7)
            pdf.setFillColor(COR_HEADER_TXT)
            pdf.drawString(sx(22 * mm), sy((y + alt - 5.5) * mm), titulo.upper())
            yy = y + alt - 12
            while yy >= y + 4:
                pdf.setStrokeColor(HexColor("#F3D1DC"))
                pdf.setLineWidth(0.15)
                pdf.line(sx(19 * mm), sy(yy * mm), sx(129 * mm), sy(yy * mm))
                yy -= 4
        pdf.showPage()

    def pagina_semanal_titulo(self, pdf):
        accent = self._theme_accent()
        pdf.setFillColor(HexColor("#FFFAF5"))
        pdf.rect(0, 0, config.LARGURA, config.ALTURA, fill=1, stroke=0)
        pw = config.LARGURA / mm
        ph = config.ALTURA / mm
        pdf.setFillColor(accent)
        pdf.roundRect(sx(8 * mm), sy((ph - 14) * mm), sx((pw - 16) * mm), sy(8 * mm), 3 * mm, fill=1, stroke=0)
        _draw_flower(pdf, pw / 2 - 35, ph - 10, 1.5, COR_PETAL_1, COR_CENTER)
        _draw_flower(pdf, pw / 2 + 35, ph - 10, 1.2, COR_PETAL_2, COR_CENTER)
        _draw_leaf(pdf, pw / 2 - 33, ph - 11, 1.5, 45, COR_LEAF)
        _draw_leaf(pdf, pw / 2 + 33, ph - 11, 1.5, 135, COR_LEAF)
        pdf.setFont(_FONT_B, 10)
        pdf.setFillColor(COR_HEADER_TXT)
        pdf.drawCentredString(sx(pw / 2 * mm), sy((ph - 10.5) * mm), "PLANEJAMENTO SEMANAL")

    def pagina_semanal_dias(self, pdf, dias_info):
        pw = config.LARGURA / mm
        ph = config.ALTURA / mm
        x = 5
        y = ph - 28
        largura = 18
        altura = 8
        espacamento = 2
        floral_colors = [HexColor("#FCE4EC"), HexColor("#F3E5F5"), HexColor("#E8F5E9"), HexColor("#FFF3E0"), HexColor("#E3F2FD"), HexColor("#FCE4EC"), HexColor("#F3E5F5")]
        for i, texto_cor in enumerate(dias_info):
            texto, cor = texto_cor
            day_color = floral_colors[i % len(floral_colors)]
            pdf.setFillColor(day_color)
            pdf.roundRect(sx(x * mm), sy(y * mm), sx(largura * mm), sy(altura * mm), 3 * mm, fill=1, stroke=0)
            pdf.setStrokeColor(HexColor("#F3D1DC"))
            pdf.setLineWidth(0.3)
            pdf.roundRect(sx(x * mm), sy(y * mm), sx(largura * mm), sy(altura * mm), 3 * mm, fill=0, stroke=1)
            pdf.setFont(_FONT_B, 7)
            pdf.setFillColor(HexColor("#6D4C5A"))
            pdf.drawCentredString(sx((x + largura / 2) * mm), sy((y + 2.5) * mm), texto)
            _draw_flower(pdf, x + largura / 2, y - 4, 1, COR_PETAL_1, COR_CENTER, 4)
            x += largura + espacamento
        self.divisor(pdf, 8, ph - 37, pw - 8)

    def pagina_semanal_prioridades(self, pdf, x, y, w, h):
        accent = self._theme_accent()
        pdf.setFillColor(HexColor("#FFF5F8"))
        pdf.setStrokeColor(HexColor("#F3D1DC"))
        pdf.setLineWidth(0.4)
        pdf.roundRect(sx(x * mm), sy(y * mm), sx(w * mm), sy(h * mm), 3 * mm, fill=1, stroke=1)
        pdf.setFillColor(accent)
        pdf.roundRect(sx(x * mm), sy((y + h - 8) * mm), sx(w * mm), sy(8 * mm), 3 * mm, fill=1, stroke=0)
        pdf.rect(sx(x * mm), sy((y + h - 5) * mm), sx(w * mm), sy(5 * mm), fill=1, stroke=0)
        _draw_flower(pdf, x + 5, y + h - 4, 1.2, COR_PETAL_1, COR_CENTER, 4)
        _draw_flower(pdf, x + w - 5, y + h - 4, 1, COR_PETAL_2, COR_CENTER, 4)
        pdf.setFont(_FONT_B, 8)
        pdf.setFillColor(COR_HEADER_TXT)
        pdf.drawCentredString(sx((x + w / 2) * mm), sy((y + h - 5.5) * mm), "PRIORIDADES DA SEMANA")
        yy = y + h - 14
        for _ in range(5):
            _draw_flower(pdf, x + 5, yy, 0.6, COR_PETAL_1, COR_CENTER, 3)
            pdf.setStrokeColor(HexColor("#F3D1DC"))
            pdf.setLineWidth(0.2)
            pdf.line(sx((x + 8) * mm), sy((yy + 0.25) * mm), sx((x + w - 4) * mm), sy((yy + 0.25) * mm))
            yy -= 5

    def pagina_semanal_escrita(self, pdf, x, y, w, h):
        accent = self._theme_accent()
        pdf.setFillColor(HexColor("#FFF5F8"))
        pdf.setStrokeColor(HexColor("#F3D1DC"))
        pdf.setLineWidth(0.4)
        pdf.roundRect(sx(x * mm), sy(y * mm), sx(w * mm), sy(h * mm), 3 * mm, fill=1, stroke=1)
        pdf.setFillColor(accent)
        pdf.roundRect(sx(x * mm), sy((y + h - 8) * mm), sx(w * mm), sy(8 * mm), 3 * mm, fill=1, stroke=0)
        pdf.rect(sx(x * mm), sy((y + h - 5) * mm), sx(w * mm), sy(5 * mm), fill=1, stroke=0)
        _draw_flower(pdf, x + w / 2 - 6, y + h - 4, 1.2, COR_PETAL_1, COR_CENTER, 4)
        _draw_flower(pdf, x + w / 2, y + h - 4, 1.5, COR_PETAL_2, COR_CENTER)
        _draw_flower(pdf, x + w / 2 + 6, y + h - 4, 1.2, COR_PETAL_1, COR_CENTER, 4)
        _draw_leaf(pdf, x + w / 2 - 9, y + h - 4, 1.5, 200, COR_LEAF)
        _draw_leaf(pdf, x + w / 2 + 9, y + h - 4, 1.5, 340, COR_LEAF)
        pdf.setFont(_FONT_B, 8)
        pdf.setFillColor(COR_HEADER_TXT)
        pdf.drawCentredString(sx((x + w / 2) * mm), sy((y + h - 5.5) * mm), "ANOTACOES")
        yy = y + h - 14
        while yy >= y + 6:
            pdf.setStrokeColor(HexColor("#F3D1DC"))
            pdf.setLineWidth(0.15)
            pdf.line(sx((x + 4) * mm), sy(yy * mm), sx((x + w - 4) * mm), sy(yy * mm))
            _draw_flower(pdf, x + 3, yy, 0.3, COR_PETAL_1, COR_CENTER, 3)
            yy -= 6

    def desenhar_logo(self, pdf):
        pass


estilo = Floral()
