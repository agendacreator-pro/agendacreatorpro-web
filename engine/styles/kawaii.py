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
import localization

_FONT_B = "Helvetica-Bold"
_FONT = "Helvetica"

tema = Tema(
    nome="Kawaii",
    primaria="#FFFFFF",
    secundaria="#FFF5FA",
    destaque="#FF69B4",
    texto="#555555",
    texto_secundario="#AAAAAA",
    linhas="#FFB6C1",
    bordas="#FFB6C1",
    cabecalho="#FF69B4",
    texto_cabecalho="#FFFFFF",
    prioridade="#FF69B4",
    mini_borda="#FFB6C1",
    mini_texto="#555555",
    mini_domingo="#FF6B8A",
    feriado="#FF6B8A",
    fonte_titulo="Helvetica-Bold",
    fonte_texto="Helvetica",
)

COR_STAR = HexColor("#FFD700")
COR_HEART = HexColor("#FF69B4")
COR_CLOUD = HexColor("#E8F4FD")
COR_HAPPY = HexColor("#FFD700")
COR_HEADER_TXT = HexColor("#FFFFFF")


def _draw_star(pdf, cx, cy, r, cor):
    pdf.setFillColor(cor)
    pdf.setStrokeColor(cor)
    pdf.setLineWidth(0.3)
    path = pdf.beginPath()
    for i in range(5):
        angle = math.radians(90 + i * 72)
        x = cx + r * math.cos(angle)
        y = cy + r * math.sin(angle)
        if i == 0:
            path.moveTo(x * mm, y * mm)
        else:
            path.lineTo(x * mm, y * mm)
        angle2 = math.radians(90 + i * 72 + 36)
        x2 = cx + r * 0.4 * math.cos(angle2)
        y2 = cy + r * 0.4 * math.sin(angle2)
        path.lineTo(x2 * mm, y2 * mm)
    path.close()
    pdf.drawPath(path, fill=1, stroke=0)


def _draw_heart(pdf, cx, cy, size, cor):
    pdf.setFillColor(cor)
    pdf.saveState()
    pdf.translate(cx * mm, cy * mm)
    p = pdf.beginPath()
    s = size * 0.5
    p.moveTo(0, s * 0.3 * mm)
    p.curveTo(s * 0.5 * mm, s * 0.8 * mm, s * 0.8 * mm, s * 0.2 * mm, 0, -s * 0.5 * mm)
    p.moveTo(0, s * 0.3 * mm)
    p.curveTo(-s * 0.5 * mm, s * 0.8 * mm, -s * 0.8 * mm, s * 0.2 * mm, 0, -s * 0.5 * mm)
    pdf.drawPath(p, fill=1, stroke=0)
    pdf.restoreState()


def _draw_cloud(pdf, cx, cy, w, h, cor):
    pdf.setFillColor(cor)
    pdf.circle(cx * mm, cy * mm, w * 0.25 * mm, fill=1, stroke=0)
    pdf.circle((cx - w * 0.15) * mm, (cy - h * 0.1) * mm, w * 0.2 * mm, fill=1, stroke=0)
    pdf.circle((cx + w * 0.15) * mm, (cy - h * 0.1) * mm, w * 0.2 * mm, fill=1, stroke=0)
    pdf.rect((cx - w * 0.25) * mm, (cy - h * 0.2) * mm, w * 0.5 * mm, h * 0.15 * mm, fill=1, stroke=0)


def _draw_happy_face(pdf, cx, cy, r, cor):
    pdf.setFillColor(cor)
    pdf.circle(cx * mm, cy * mm, r * mm, fill=1, stroke=0)
    pdf.setFillColor(HexColor("#333333"))
    pdf.circle((cx - r * 0.3) * mm, (cy + r * 0.2) * mm, r * 0.12 * mm, fill=1, stroke=0)
    pdf.circle((cx + r * 0.3) * mm, (cy + r * 0.2) * mm, r * 0.12 * mm, fill=1, stroke=0)
    pdf.setStrokeColor(HexColor("#333333"))
    pdf.setLineWidth(0.3)
    pdf.arc(
        (cx - r * 0.3) * mm, (cy - r * 0.2) * mm,
        (cx + r * 0.3) * mm, (cy + r * 0.15) * mm,
        200, 140
    )


class Kawaii(EstiloBase):
    nome = "Kawaii"

    def fundo_pagina(self, pdf):
        pdf.setFillColor(HexColor("#FFF5FA"))
        pdf.rect(0, 0, config.LARGURA, config.ALTURA, fill=1, stroke=0)

    def faixa_mes(self, pdf, x, y, w, h, data):
        accent = self._theme_accent()
        pdf.setFillColor(accent)
        pdf.roundRect(sx(x * mm), sy(y * mm), sx(w * mm), sy(h * mm), 4 * mm, fill=1, stroke=0)
        pdf.saveState()
        cx = sx((x + w / 2) * mm)
        cy = sy((y + h / 2) * mm)
        pdf.translate(cx, cy)
        pdf.rotate(90)
        pdf.setFont(_FONT_B, 9)
        pdf.setFillColor(COR_HEADER_TXT)
        pdf.drawCentredString(0, 0, localization.nome_mes(data.month).upper())
        pdf.restoreState()
        _draw_star(pdf, x + w / 2 - 6, y + h / 2, 1.2, COR_STAR)

    def cabecalho_diario(self, pdf, data, x, y, w, h, is_2dpp=False, espelhar=False):
        accent = self._theme_accent()
        pdf.setFillColor(HexColor("#FFF5FA"))
        pdf.roundRect(sx(x * mm), sy(y * mm), sx(w * mm), sy(h * mm), 5 * mm, fill=1, stroke=0)
        if is_2dpp:
            pdf.setFillColor(accent)
            pdf.roundRect(sx(x * mm), sy((y + h - 12) * mm), sx(w * mm), sy(12 * mm), 5 * mm, fill=1, stroke=0)
            pdf.rect(sx(x * mm), sy((y + h - 8) * mm), sx(w * mm), sy(8 * mm), fill=1, stroke=0)
            _draw_heart(pdf, x + w - 6, y + h - 6, 1.5, COR_HEART)
            pdf.setFont(_FONT_B, 18)
            pdf.setFillColor(BRANCO)
            pdf.drawString(sx((x + 3) * mm), sy((y + h - 9) * mm), data.strftime("%d"))
            if espelhar:
                pdf.setFont(_FONT_B, 9)
                pdf.setFillColor(HexColor("#FF69B4"))
                pdf.drawString(sx((x + 3) * mm), sy((y + 5) * mm), localization.nome_dia(data).upper())
                pdf.setFont(_FONT, 7)
                pdf.setFillColor(HexColor("#CC6699"))
                pdf.drawString(sx((x + 3) * mm), sy((y + 1) * mm), data.strftime("%d/%m/%Y"))
                _draw_happy_face(pdf, x + w - 6, y + 4, 1.5, COR_HAPPY)
            else:
                pdf.setFont(_FONT_B, 9)
                pdf.setFillColor(HexColor("#FF69B4"))
                pdf.drawRightString(sx((x + w - 3) * mm), sy((y + 6) * mm), localization.nome_dia(data).upper())
                pdf.setFont(_FONT, 7)
                pdf.setFillColor(HexColor("#CC6699"))
                pdf.drawRightString(sx((x + w - 3) * mm), sy((y + 1) * mm), data.strftime("%d/%m/%Y"))
                _draw_happy_face(pdf, x + 8, y + 4, 2, COR_HAPPY)
        else:
            pdf.setFillColor(accent)
            pdf.roundRect(sx(x * mm), sy((y + h - 14) * mm), sx(w * mm), sy(14 * mm), 5 * mm, fill=1, stroke=0)
            pdf.rect(sx(x * mm), sy((y + h - 10) * mm), sx(w * mm), sy(10 * mm), fill=1, stroke=0)
            _draw_heart(pdf, x + w - 8, y + h - 7, 2, COR_HEART)
            pdf.setFont(_FONT_B, 44)
            pdf.setFillColor(BRANCO)
            pdf.drawRightString(sx((x + w - 5) * mm), sy((y + 14) * mm), data.strftime("%d"))
            pdf.setFont(_FONT_B, 10)
            pdf.setFillColor(HexColor("#FF69B4"))
            pdf.drawRightString(sx((x + w - 5) * mm), sy((y + 6) * mm), localization.nome_dia(data).upper())
            pdf.setFont(_FONT, 7)
            pdf.setFillColor(HexColor("#CC6699"))
            pdf.drawRightString(sx((x + w - 5) * mm), sy((y + 1) * mm), data.strftime("%d/%m/%Y"))
            _draw_happy_face(pdf, x + 8, y + 4, 2.5, COR_HAPPY)

    def caixa_prioridades(self, pdf, x, y, w, h):
        accent = self._theme_accent()
        pdf.setFillColor(HexColor("#FFF0F5"))
        pdf.setStrokeColor(HexColor("#FFD1DC"))
        pdf.setLineWidth(0.8)
        pdf.roundRect(sx(x * mm), sy(y * mm), sx(w * mm), sy(h * mm), 4 * mm, fill=1, stroke=1)
        pdf.setFillColor(accent)
        pdf.roundRect(sx(x * mm), sy((y + h - 9) * mm), sx(w * mm), sy(9 * mm), 4 * mm, fill=1, stroke=0)
        pdf.rect(sx(x * mm), sy((y + h - 6) * mm), sx(w * mm), sy(6 * mm), fill=1, stroke=0)
        _draw_star(pdf, x + 5, y + h - 4.5, 1.5, COR_STAR)
        _draw_heart(pdf, x + w - 5, y + h - 4.5, 1.2, COR_HEART)
        pdf.setFont(_FONT_B, 8)
        pdf.setFillColor(COR_HEADER_TXT)
        pdf.drawCentredString(sx((x + w / 2) * mm), sy((y + h - 6.5) * mm), localization.label("prioridades"))
        espacamento = (h - 14) / 4
        yy = y + h - 14
        dot_colors = [accent, HexColor("#FFB6C1"), HexColor("#FF85A2"), HexColor("#FFC0CB")]
        for cor in dot_colors:
            pdf.setFillColor(cor)
            pdf.circle(sx((x + 7) * mm), sy(yy * mm), 1.0 * mm, fill=1, stroke=0)
            pdf.setStrokeColor(HexColor("#FFE4EC"))
            pdf.setDash([1.0, 0.8], 0)
            pdf.setLineWidth(0.3)
            pdf.line(sx((x + 10) * mm), sy(yy * mm), sx((x + w - 5) * mm), sy(yy * mm))
            pdf.setDash([], 0)
            yy -= espacamento

    def area_anotacoes(self, pdf, x, y, w, h, num_linhas=8, com_agendamentos=False):
        accent = self._theme_accent()
        pdf.setFillColor(HexColor("#FFF0F5"))
        pdf.setStrokeColor(HexColor("#FFD1DC"))
        pdf.setLineWidth(0.6)
        pdf.roundRect(sx(x * mm), sy(y * mm), sx(w * mm), sy(h * mm), 4 * mm, fill=1, stroke=1)
        pdf.setFillColor(accent)
        pdf.roundRect(sx(x * mm), sy((y + h - 8) * mm), sx(w * mm), sy(8 * mm), 4 * mm, fill=1, stroke=0)
        pdf.rect(sx(x * mm), sy((y + h - 5) * mm), sx(w * mm), sy(5 * mm), fill=1, stroke=0)
        _draw_cloud(pdf, x + w / 2, y + h - 4, 8, 4, COR_CLOUD)
        pdf.setFont(_FONT_B, 7)
        pdf.setFillColor(COR_HEADER_TXT)
        pdf.drawCentredString(sx((x + w / 2) * mm), sy((y + h - 5.5) * mm), localization.label("anotacoes"))

        if com_agendamentos:
            header_h = 8
            body_y = y
            body_h = h - header_h
            notes_w = w * 0.65
            sched_x = x + notes_w + 2
            sched_w = w - notes_w - 2

            pdf.setStrokeColor(HexColor("#FFD1DC"))
            pdf.setLineWidth(0.3)
            pdf.line(sx(sched_x * mm), sy((y + h) * mm), sx(sched_x * mm), sy((body_y + header_h) * mm))

            pdf.setFont(_FONT_B, 7)
            pdf.setFillColor(accent)
            pdf.drawString(sx((sched_x + 1) * mm), sy((y + h - 5) * mm), localization.label("agendamentos"))

            slot_h = (body_h - 4) / 11
            for i in range(11):
                hora = 8 + i
                slot_y = y + body_h - 1.5 - i * slot_h
                pdf.setFont(_FONT_B, 5.5)
                pdf.setFillColor(accent)
                pdf.drawString(sx((sched_x + 1) * mm), sy((slot_y - 1) * mm), f"{hora:02d}:00")
                pdf.setStrokeColor(HexColor("#FFD1DC"))
                pdf.setDash([1.0, 0.8], 0)
                pdf.setLineWidth(0.2)
                pdf.line(sx((sched_x + 12) * mm), sy((slot_y - 1.5) * mm), sx((x + w - 1) * mm), sy((slot_y - 1.5) * mm))
                pdf.setDash([], 0)

            espacamento = (body_h - 4) / (num_linhas + 1)
            yy = y + body_h
            for i in range(num_linhas):
                pdf.setStrokeColor(HexColor("#FFD1DC"))
                pdf.setDash([1.0, 0.8], 0)
                pdf.setLineWidth(0.25)
                pdf.line(sx((x + 4) * mm), sy(yy * mm), sx((sched_x - 2) * mm), sy(yy * mm))
                pdf.setDash([], 0)
                yy -= espacamento
        else:
            espacamento = (h - 12) / (num_linhas + 1)
            yy = y + h - 12
            for i in range(num_linhas):
                pdf.setStrokeColor(HexColor("#FFD1DC"))
                pdf.setDash([1.0, 0.8], 0)
                pdf.setLineWidth(0.25)
                pdf.line(sx((x + 4) * mm), sy(yy * mm), sx((x + w - 4) * mm), sy(yy * mm))
                pdf.setDash([], 0)
                yy -= espacamento

    def divisor(self, pdf, x1, y, x2):
        mid = (x1 + x2) / 2
        pdf.setStrokeColor(HexColor("#FFD1DC"))
        pdf.setDash([1.0, 0.8], 0)
        pdf.setLineWidth(0.4)
        pdf.line(sx(x1 * mm), sy(y * mm), sx((mid - 2) * mm), sy(y * mm))
        pdf.line(sx((mid + 2) * mm), sy(y * mm), sx(x2 * mm), sy(y * mm))
        pdf.setDash([], 0)
        _draw_heart(pdf, mid, y, 1.2, COR_HEART)

    def decorar_canto(self, pdf, x, y, corner="tl"):
        _draw_star(pdf, x, y, 2, COR_STAR)

    def decorar_borda(self, pdf):
        pw = config.LARGURA / mm
        ph = config.ALTURA / mm
        pdf.setStrokeColor(HexColor("#FFD1DC"))
        pdf.setLineWidth(0.5)
        pdf.roundRect(sx(5 * mm), sy(5 * mm), sx((pw - 10) * mm), sy((ph - 10) * mm), 5 * mm, fill=0, stroke=1)
        _draw_star(pdf, 8, ph - 8, 2.5, COR_STAR)
        _draw_heart(pdf, pw - 8, ph - 8, 2, COR_HEART)
        _draw_cloud(pdf, 8, 8, 6, 3, COR_CLOUD)
        _draw_happy_face(pdf, pw - 8, 8, 2, COR_HAPPY)

    def pagina_dados_pessoais(self, pdf, campos):
        self.decorar_borda(pdf)
        self.fundo_pagina(pdf)
        accent = self._theme_accent()
        pw = config.LARGURA / mm
        ph = config.ALTURA / mm
        pdf.setFillColor(accent)
        pdf.roundRect(sx(15 * mm), sy((ph - 35) * mm), sx((pw - 30) * mm), sy(18 * mm), 5 * mm, fill=1, stroke=0)
        _draw_star(pdf, pw / 2 - 35, ph - 26, 3, COR_STAR)
        _draw_heart(pdf, pw / 2 + 35, ph - 26, 2.5, COR_HEART)
        pdf.setFont(_FONT_B, 18)
        pdf.setFillColor(COR_HEADER_TXT)
        pdf.drawCentredString(sx(pw / 2 * mm), sy((ph - 27) * mm), localization.label("dados_pessoais"))
        yy = ph - 50
        for campo in campos:
            pdf.setFont(_FONT_B, 8)
            pdf.setFillColor(HexColor("#FF69B4"))
            pdf.drawString(sx(20 * mm), sy(yy * mm), campo)
            pdf.setStrokeColor(HexColor("#FFD1DC"))
            pdf.setDash([1.0, 0.8], 0)
            pdf.setLineWidth(0.3)
            pdf.line(sx(20 * mm), sy((yy - 2) * mm), sx((pw - 20) * mm), sy((yy - 2) * mm))
            pdf.setDash([], 0)
            _draw_heart(pdf, 18, yy - 1, 0.6, COR_HEART)
            yy -= 18
        pdf.showPage()

    def planejamento(self, pdf, caixas):
        self.decorar_borda(pdf)
        self.fundo_pagina(pdf)
        accent = self._theme_accent()
        pw = config.LARGURA / mm
        ph = config.ALTURA / mm
        pdf.setFillColor(accent)
        pdf.roundRect(sx(10 * mm), sy((ph - 28) * mm), sx((pw - 20) * mm), sy(14 * mm), 5 * mm, fill=1, stroke=0)
        _draw_star(pdf, pw / 2 - 40, ph - 21, 2.5, COR_STAR)
        _draw_cloud(pdf, pw / 2 + 40, ph - 21, 6, 3, COR_CLOUD)
        pdf.setFont(_FONT_B, 16)
        pdf.setFillColor(COR_HEADER_TXT)
        pdf.drawCentredString(sx(pw / 2 * mm), sy((ph - 22) * mm), "PLANEJAMENTO ANUAL")
        pdf.setFont(_FONT, 8)
        pdf.setFillColor(HexColor("#CC6699"))
        pdf.drawCentredString(sx(pw / 2 * mm), sy((ph - 33) * mm), "Metas e Objetivos")
        for titulo, y, alt in caixas:
            pdf.setFillColor(HexColor("#FFF0F5"))
            pdf.setStrokeColor(HexColor("#FFD1DC"))
            pdf.setLineWidth(0.5)
            pdf.roundRect(sx(15 * mm), sy(y * mm), sx(118 * mm), sy(alt * mm), 4 * mm, fill=1, stroke=1)
            pdf.setFillColor(accent)
            pdf.roundRect(sx(15 * mm), sy((y + alt - 8) * mm), sx(118 * mm), sy(8 * mm), 4 * mm, fill=1, stroke=0)
            pdf.rect(sx(15 * mm), sy((y + alt - 5) * mm), sx(118 * mm), sy(5 * mm), fill=1, stroke=0)
            _draw_star(pdf, 18, y + alt - 4, 1.2, COR_STAR)
            pdf.setFont(_FONT_B, 7)
            pdf.setFillColor(COR_HEADER_TXT)
            pdf.drawString(sx(22 * mm), sy((y + alt - 5.5) * mm), titulo.upper())
            yy = y + alt - 12
            while yy >= y + 4:
                pdf.setStrokeColor(HexColor("#FFD1DC"))
                pdf.setDash([1.0, 0.8], 0)
                pdf.setLineWidth(0.15)
                pdf.line(sx(19 * mm), sy(yy * mm), sx(129 * mm), sy(yy * mm))
                pdf.setDash([], 0)
                yy -= 4
        pdf.showPage()

    def pagina_semanal_titulo(self, pdf):
        accent = self._theme_accent()
        pdf.setFillColor(HexColor("#FFF5FA"))
        pdf.rect(0, 0, config.LARGURA, config.ALTURA, fill=1, stroke=0)
        pw = config.LARGURA / mm
        ph = config.ALTURA / mm
        pdf.setFillColor(accent)
        pdf.roundRect(sx(8 * mm), sy((ph - 14) * mm), sx((pw - 16) * mm), sy(8 * mm), 4 * mm, fill=1, stroke=0)
        _draw_star(pdf, pw / 2 - 35, ph - 10, 1.5, COR_STAR)
        _draw_heart(pdf, pw / 2 + 35, ph - 10, 1.2, COR_HEART)
        pdf.setFont(_FONT_B, 10)
        pdf.setFillColor(COR_HEADER_TXT)
        pdf.drawCentredString(sx(pw / 2 * mm), sy((ph - 10.5) * mm), localization.label("planejamento_semanal"))

    def pagina_semanal_dias(self, pdf, dias_info):
        pw = config.LARGURA / mm
        ph = config.ALTURA / mm
        x = 5
        y = ph - 28
        largura = 18
        altura = 8
        espacamento = 2
        kawaii_colors = [HexColor("#FFB6C1"), HexColor("#FFDAC1"), HexColor("#B5EAD7"), HexColor("#C7CEEA"), HexColor("#FFB6C1"), HexColor("#FFDAC1"), HexColor("#B5EAD7")]
        for i, texto_cor in enumerate(dias_info):
            texto, cor = texto_cor
            day_color = kawaii_colors[i % len(kawaii_colors)]
            pdf.setFillColor(day_color)
            pdf.roundRect(sx(x * mm), sy(y * mm), sx(largura * mm), sy(altura * mm), 3 * mm, fill=1, stroke=0)
            pdf.setFont(_FONT_B, 7)
            pdf.setFillColor(HexColor("#555555"))
            pdf.drawCentredString(sx((x + largura / 2) * mm), sy((y + 2.5) * mm), texto)
            _draw_happy_face(pdf, x + largura / 2, y - 4, 1.2, COR_HAPPY)
            x += largura + espacamento
        self.divisor(pdf, 8, ph - 37, pw - 8)

    def pagina_semanal_prioridades(self, pdf, x, y, w, h):
        accent = self._theme_accent()
        pdf.setFillColor(HexColor("#FFF0F5"))
        pdf.setStrokeColor(HexColor("#FFD1DC"))
        pdf.setLineWidth(0.5)
        pdf.roundRect(sx(x * mm), sy(y * mm), sx(w * mm), sy(h * mm), 4 * mm, fill=1, stroke=1)
        pdf.setFillColor(accent)
        pdf.roundRect(sx(x * mm), sy((y + h - 8) * mm), sx(w * mm), sy(8 * mm), 4 * mm, fill=1, stroke=0)
        pdf.rect(sx(x * mm), sy((y + h - 5) * mm), sx(w * mm), sy(5 * mm), fill=1, stroke=0)
        _draw_star(pdf, x + 5, y + h - 4, 1.2, COR_STAR)
        pdf.setFont(_FONT_B, 8)
        pdf.setFillColor(COR_HEADER_TXT)
        pdf.drawCentredString(sx((x + w / 2) * mm), sy((y + h - 5.5) * mm), "PRIORIDADES DA SEMANA")
        yy = y + h - 14
        for _ in range(5):
            pdf.setFillColor(HexColor("#FFB6C1"))
            pdf.circle(sx((x + 5) * mm), sy(yy * mm), 0.8 * mm, fill=1, stroke=0)
            pdf.setStrokeColor(HexColor("#FFD1DC"))
            pdf.setDash([1.0, 0.8], 0)
            pdf.setLineWidth(0.2)
            pdf.line(sx((x + 8) * mm), sy((yy + 0.25) * mm), sx((x + w - 4) * mm), sy((yy + 0.25) * mm))
            pdf.setDash([], 0)
            yy -= 5

    def pagina_semanal_escrita(self, pdf, x, y, w, h):
        accent = self._theme_accent()
        pdf.setFillColor(HexColor("#FFF0F5"))
        pdf.setStrokeColor(HexColor("#FFD1DC"))
        pdf.setLineWidth(0.5)
        pdf.roundRect(sx(x * mm), sy(y * mm), sx(w * mm), sy(h * mm), 4 * mm, fill=1, stroke=1)
        pdf.setFillColor(accent)
        pdf.roundRect(sx(x * mm), sy((y + h - 8) * mm), sx(w * mm), sy(8 * mm), 4 * mm, fill=1, stroke=0)
        pdf.rect(sx(x * mm), sy((y + h - 5) * mm), sx(w * mm), sy(5 * mm), fill=1, stroke=0)
        _draw_cloud(pdf, x + w / 2, y + h - 4, 6, 3, COR_CLOUD)
        pdf.setFont(_FONT_B, 8)
        pdf.setFillColor(COR_HEADER_TXT)
        pdf.drawCentredString(sx((x + w / 2) * mm), sy((y + h - 5.5) * mm), localization.label("anotacoes"))
        yy = y + h - 14
        while yy >= y + 6:
            pdf.setStrokeColor(HexColor("#FFD1DC"))
            pdf.setDash([1.0, 0.8], 0)
            pdf.setLineWidth(0.15)
            pdf.line(sx((x + 4) * mm), sy(yy * mm), sx((x + w - 4) * mm), sy(yy * mm))
            pdf.setDash([], 0)
            yy -= 6

    def desenhar_logo(self, pdf):
        pass


estilo = Kawaii()
