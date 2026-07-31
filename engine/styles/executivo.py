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
    nome="Executivo",
    primaria="#FFFFFF",
    secundaria="#F0F2F5",
    destaque="#1A2744",
    texto="#1A2744",
    texto_secundario="#6B7280",
    linhas="#CBD5E1",
    bordas="#94A3B8",
    cabecalho="#1A2744",
    texto_cabecalho="#FFFFFF",
    prioridade="#1A2744",
    mini_borda="#CBD5E1",
    mini_texto="#1A2744",
    mini_domingo="#DC2626",
    feriado="#DC2626",
    fonte_titulo="Helvetica-Bold",
    fonte_texto="Helvetica",
)

COR_GOLD = HexColor("#B8860B")
COR_HEADER_TXT = HexColor("#FFFFFF")


class Executivo(EstiloBase):
    nome = "Executivo"

    def fundo_pagina(self, pdf):
        pdf.setFillColor(BRANCO)
        pdf.rect(0, 0, config.LARGURA, config.ALTURA, fill=1, stroke=0)

    def faixa_mes(self, pdf, x, y, w, h, data):
        accent = self._theme_accent()
        pdf.setFillColor(accent)
        pdf.rect(sx(x * mm), sy(y * mm), sx(w * mm), sy(h * mm), fill=1, stroke=0)
        pdf.setFillColor(COR_GOLD)
        pdf.rect(sx((x + w - 1.5) * mm), sy(y * mm), sx(1.5 * mm), sy(h * mm), fill=1, stroke=0)
        pdf.saveState()
        cx = sx((x + w / 2 - 0.5) * mm)
        cy = sy((y + h / 2) * mm)
        pdf.translate(cx, cy)
        pdf.rotate(90)
        pdf.setFont(_FONT_B, 9)
        pdf.setFillColor(COR_HEADER_TXT)
        pdf.drawCentredString(0, 0, localization.nome_mes(data.month).upper())
        pdf.restoreState()

    def cabecalho_diario(self, pdf, data, x, y, w, h, is_2dpp=False, espelhar=False):
        accent = self._theme_accent()
        pdf.setFillColor(BRANCO)
        pdf.rect(sx(x * mm), sy(y * mm), sx(w * mm), sy(h * mm), fill=1, stroke=0)
        if is_2dpp:
            pdf.setFillColor(accent)
            pdf.rect(sx(x * mm), sy((y + h - 10) * mm), sx(w * mm), sy(10 * mm), fill=1, stroke=0)
            pdf.setFont(_FONT_B, 16)
            pdf.setFillColor(BRANCO)
            pdf.drawString(sx((x + 3) * mm), sy((y + h - 8) * mm), data.strftime("%d"))
            if espelhar:
                pdf.setFont(_FONT_B, 9)
                pdf.setFillColor(HexColor("#374151"))
                pdf.drawString(sx((x + 3) * mm), sy((y + 6) * mm), localization.nome_dia(data).upper())
                pdf.setFont(_FONT, 7)
                pdf.setFillColor(HexColor("#6B7280"))
                pdf.drawString(sx((x + 3) * mm), sy((y + 1) * mm), data.strftime("%d/%m/%Y"))
            else:
                pdf.setFont(_FONT_B, 9)
                pdf.setFillColor(HexColor("#374151"))
                pdf.drawRightString(sx((x + w - 3) * mm), sy((y + 10) * mm), localization.nome_dia(data).upper())
                pdf.setFont(_FONT, 7)
                pdf.setFillColor(HexColor("#6B7280"))
                pdf.drawRightString(sx((x + w - 3) * mm), sy((y + 3) * mm), data.strftime("%d/%m/%Y"))
        else:
            pdf.setFillColor(accent)
            pdf.rect(sx(x * mm), sy((y + h - 12) * mm), sx(w * mm), sy(12 * mm), fill=1, stroke=0)
            pdf.setFont(_FONT_B, 28)
            pdf.setFillColor(BRANCO)
            pdf.drawRightString(sx((x + w - 5) * mm), sy((y + h - 6) * mm), data.strftime("%d"))
            pdf.setFont(_FONT_B, 10)
            pdf.setFillColor(HexColor("#374151"))
            pdf.drawRightString(sx((x + w - 5) * mm), sy((y + 16) * mm), localization.nome_dia(data).upper())
            pdf.setFont(_FONT, 7)
            pdf.setFillColor(HexColor("#6B7280"))
            pdf.drawRightString(sx((x + w - 5) * mm), sy((y + 8) * mm), data.strftime("%d/%m/%Y"))
        pdf.setStrokeColor(HexColor("#CBD5E1"))
        pdf.setLineWidth(0.6)
        pdf.line(sx(x * mm), sy(y * mm), sx((x + w) * mm), sy(y * mm))
        pdf.setFillColor(COR_GOLD)
        pdf.rect(sx(x * mm), sy(y * mm), sx(w * mm), sy(0.8 * mm), fill=1, stroke=0)

    def caixa_prioridades(self, pdf, x, y, w, h):
        accent = self._theme_accent()
        task = self._theme_tasks()
        pdf.setFillColor(HexColor("#F8FAFC"))
        pdf.setStrokeColor(HexColor("#94A3B8"))
        pdf.setLineWidth(0.5)
        pdf.rect(sx(x * mm), sy(y * mm), sx(w * mm), sy(h * mm), fill=1, stroke=1)
        pdf.setFillColor(accent)
        pdf.rect(sx(x * mm), sy((y + h - 9) * mm), sx(w * mm), sy(9 * mm), fill=1, stroke=0)
        pdf.setFillColor(COR_GOLD)
        pdf.rect(sx(x * mm), sy((y + h - 9) * mm), sx(2.5 * mm), sy(9 * mm), fill=1, stroke=0)
        pdf.setFont(_FONT_B, 8)
        pdf.setFillColor(COR_HEADER_TXT)
        pdf.drawString(sx((x + 6) * mm), sy((y + h - 6.5) * mm), localization.label("prioridades"))
        espacamento = (h - 14) / 4
        yy = y + h - 14
        dot_colors = [accent, task, HexColor("#059669"), HexColor("#D97706")]
        for cor in dot_colors:
            pdf.setFillColor(cor)
            pdf.rect(sx((x + 5) * mm), sy((yy - 1) * mm), sx(3 * mm), sy(2 * mm), fill=1, stroke=0)
            pdf.setStrokeColor(HexColor("#E2E8F0"))
            pdf.setLineWidth(0.3)
            pdf.line(sx((x + 10) * mm), sy(yy * mm), sx((x + w - 4) * mm), sy(yy * mm))
            yy -= espacamento

    def area_anotacoes(self, pdf, x, y, w, h, num_linhas=8, com_agendamentos=False):
        accent = self._theme_accent()
        pdf.setFillColor(HexColor("#F8FAFC"))
        pdf.setStrokeColor(HexColor("#94A3B8"))
        pdf.setLineWidth(0.4)
        pdf.rect(sx(x * mm), sy(y * mm), sx(w * mm), sy(h * mm), fill=1, stroke=1)
        pdf.setFillColor(accent)
        pdf.rect(sx(x * mm), sy((y + h - 7) * mm), sx(w * mm), sy(7 * mm), fill=1, stroke=0)
        pdf.setFillColor(COR_GOLD)
        pdf.rect(sx(x * mm), sy((y + h - 7) * mm), sx(2 * mm), sy(7 * mm), fill=1, stroke=0)
        pdf.setFont(_FONT_B, 7)
        pdf.setFillColor(COR_HEADER_TXT)
        pdf.drawString(sx((x + 5) * mm), sy((y + h - 5) * mm), localization.label("anotacoes"))

        if com_agendamentos:
            header_h = 7
            body_y = y
            body_h = h - header_h
            notes_w = w * 0.65
            sched_x = x + notes_w + 2
            sched_w = w - notes_w - 2

            pdf.setStrokeColor(HexColor("#94A3B8"))
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
                pdf.setStrokeColor(HexColor("#E2E8F0"))
                pdf.setLineWidth(0.2)
                pdf.line(sx((sched_x + 12) * mm), sy((slot_y - 1.5) * mm), sx((x + w - 1) * mm), sy((slot_y - 1.5) * mm))

            espacamento = (body_h - 4) / (num_linhas + 1)
            yy = y + body_h
            for _ in range(num_linhas):
                pdf.setStrokeColor(HexColor("#E2E8F0"))
                pdf.setLineWidth(0.2)
                pdf.line(sx((x + 4) * mm), sy(yy * mm), sx((sched_x - 2) * mm), sy(yy * mm))
                yy -= espacamento
        else:
            espacamento = (h - 12) / (num_linhas + 1)
            yy = y + h - 12
            for _ in range(num_linhas):
                pdf.setStrokeColor(HexColor("#E2E8F0"))
                pdf.setLineWidth(0.2)
                pdf.line(sx((x + 4) * mm), sy(yy * mm), sx((x + w - 4) * mm), sy(yy * mm))
                yy -= espacamento

    def divisor(self, pdf, x1, y, x2):
        pdf.setStrokeColor(HexColor("#CBD5E1"))
        pdf.setLineWidth(0.5)
        pdf.line(sx(x1 * mm), sy(y * mm), sx(x2 * mm), sy(y * mm))

    def decorar_canto(self, pdf, x, y, corner="tl"):
        pdf.setStrokeColor(COR_GOLD)
        pdf.setLineWidth(0.4)
        sz = 4
        if corner == "tl":
            pdf.line(sx(x * mm), sy(y * mm), sx((x + sz) * mm), sy(y * mm))
            pdf.line(sx(x * mm), sy(y * mm), sx(x * mm), sy((y - sz) * mm))
        elif corner == "tr":
            pdf.line(sx((x - sz) * mm), sy(y * mm), sx(x * mm), sy(y * mm))
            pdf.line(sx(x * mm), sy(y * mm), sx(x * mm), sy((y - sz) * mm))
        elif corner == "bl":
            pdf.line(sx(x * mm), sy(y * mm), sx((x + sz) * mm), sy(y * mm))
            pdf.line(sx(x * mm), sy(y * mm), sx(x * mm), sy((y + sz) * mm))
        elif corner == "br":
            pdf.line(sx((x - sz) * mm), sy(y * mm), sx(x * mm), sy(y * mm))
            pdf.line(sx(x * mm), sy(y * mm), sx(x * mm), sy((y + sz) * mm))

    def decorar_borda(self, pdf):
        pw = config.LARGURA / mm
        ph = config.ALTURA / mm
        pdf.setStrokeColor(HexColor("#CBD5E1"))
        pdf.setLineWidth(0.4)
        pdf.rect(sx(5 * mm), sy(5 * mm), sx((pw - 10) * mm), sy((ph - 10) * mm), fill=0, stroke=1)
        self.decorar_canto(pdf, 5, ph - 5, "tl")
        self.decorar_canto(pdf, pw - 5, ph - 5, "tr")
        self.decorar_canto(pdf, 5, 5, "bl")
        self.decorar_canto(pdf, pw - 5, 5, "br")

    def pagina_dados_pessoais(self, pdf, campos):
        self.decorar_borda(pdf)
        self.fundo_pagina(pdf)
        accent = self._theme_accent()
        pw = config.LARGURA / mm
        ph = config.ALTURA / mm
        pdf.setFillColor(accent)
        pdf.rect(sx(15 * mm), sy((ph - 35) * mm), sx((pw - 30) * mm), sy(18 * mm), fill=1, stroke=0)
        pdf.setFillColor(COR_GOLD)
        pdf.rect(sx(15 * mm), sy((ph - 35) * mm), sx(3 * mm), sy(18 * mm), fill=1, stroke=0)
        pdf.setFont(_FONT_B, 18)
        pdf.setFillColor(COR_HEADER_TXT)
        pdf.drawCentredString(sx(pw / 2 * mm), sy((ph - 27) * mm), localization.label("dados_pessoais"))
        yy = ph - 50
        for campo in campos:
            pdf.setFont(_FONT_B, 8)
            pdf.setFillColor(HexColor("#374151"))
            pdf.drawString(sx(20 * mm), sy(yy * mm), campo.upper())
            pdf.setStrokeColor(HexColor("#CBD5E1"))
            pdf.setLineWidth(0.3)
            pdf.line(sx(20 * mm), sy((yy - 2) * mm), sx((pw - 20) * mm), sy((yy - 2) * mm))
            pdf.setFillColor(COR_GOLD)
            pdf.rect(sx(20 * mm), sy((yy - 2) * mm), sx(1.5 * mm), sy(0.3 * mm), fill=1, stroke=0)
            yy -= 18
        pdf.showPage()

    def planejamento(self, pdf, caixas):
        self.decorar_borda(pdf)
        self.fundo_pagina(pdf)
        accent = self._theme_accent()
        pw = config.LARGURA / mm
        ph = config.ALTURA / mm
        pdf.setFillColor(accent)
        pdf.rect(sx(10 * mm), sy((ph - 28) * mm), sx((pw - 20) * mm), sy(14 * mm), fill=1, stroke=0)
        pdf.setFillColor(COR_GOLD)
        pdf.rect(sx(10 * mm), sy((ph - 28) * mm), sx(2.5 * mm), sy(14 * mm), fill=1, stroke=0)
        pdf.setFont(_FONT_B, 16)
        pdf.setFillColor(COR_HEADER_TXT)
        pdf.drawCentredString(sx(pw / 2 * mm), sy((ph - 22) * mm), "PLANEJAMENTO ANUAL")
        pdf.setFont(_FONT, 8)
        pdf.setFillColor(HexColor("#6B7280"))
        pdf.drawCentredString(sx(pw / 2 * mm), sy((ph - 33) * mm), "Metas e Objetivos")
        for titulo, y, alt in caixas:
            pdf.setFillColor(HexColor("#F8FAFC"))
            pdf.setStrokeColor(HexColor("#94A3B8"))
            pdf.setLineWidth(0.4)
            pdf.rect(sx(15 * mm), sy(y * mm), sx(118 * mm), sy(alt * mm), fill=1, stroke=1)
            pdf.setFillColor(accent)
            pdf.rect(sx(15 * mm), sy((y + alt - 8) * mm), sx(118 * mm), sy(8 * mm), fill=1, stroke=0)
            pdf.setFillColor(COR_GOLD)
            pdf.rect(sx(15 * mm), sy((y + alt - 8) * mm), sx(2 * mm), sy(8 * mm), fill=1, stroke=0)
            pdf.setFont(_FONT_B, 7)
            pdf.setFillColor(COR_HEADER_TXT)
            pdf.drawString(sx(19 * mm), sy((y + alt - 6) * mm), titulo.upper())
            yy = y + alt - 12
            while yy >= y + 4:
                pdf.setStrokeColor(HexColor("#E2E8F0"))
                pdf.setLineWidth(0.15)
                pdf.line(sx(19 * mm), sy(yy * mm), sx(129 * mm), sy(yy * mm))
                yy -= 4
        pdf.showPage()

    def pagina_semanal_titulo(self, pdf):
        accent = self._theme_accent()
        pdf.setFillColor(BRANCO)
        pdf.rect(0, 0, config.LARGURA, config.ALTURA, fill=1, stroke=0)
        pw = config.LARGURA / mm
        ph = config.ALTURA / mm
        pdf.setFillColor(accent)
        pdf.rect(sx(8 * mm), sy((ph - 14) * mm), sx((pw - 16) * mm), sy(8 * mm), fill=1, stroke=0)
        pdf.setFillColor(COR_GOLD)
        pdf.rect(sx(8 * mm), sy((ph - 14) * mm), sx(2.5 * mm), sy(8 * mm), fill=1, stroke=0)
        pdf.setFont(_FONT_B, 10)
        pdf.setFillColor(COR_HEADER_TXT)
        pdf.drawCentredString(sx(pw / 2 * mm), sy((ph - 10.5) * mm), localization.label("planejamento_semanal"))

    def pagina_semanal_dias(self, pdf, dias_info):
        accent = self._theme_accent()
        pw = config.LARGURA / mm
        ph = config.ALTURA / mm
        x = 5
        y = ph - 28
        largura = 18
        altura = 8
        espacamento = 2
        for texto_cor in dias_info:
            texto, cor = texto_cor
            pdf.setFillColor(HexColor("#E8EDF4"))
            pdf.rect(sx(x * mm), sy(y * mm), sx(largura * mm), sy(altura * mm), fill=1, stroke=0)
            pdf.setStrokeColor(HexColor("#CBD5E1"))
            pdf.setLineWidth(0.3)
            pdf.rect(sx(x * mm), sy(y * mm), sx(largura * mm), sy(altura * mm), fill=0, stroke=1)
            pdf.setFont(_FONT_B, 7)
            pdf.setFillColor(HexColor("#1A2744"))
            pdf.drawCentredString(sx((x + largura / 2) * mm), sy((y + 2.5) * mm), texto)
            pdf.setFillColor(COR_GOLD)
            pdf.circle(sx((x + largura / 2) * mm), sy((y - 4) * mm), 1.0 * mm, fill=1, stroke=0)
            x += largura + espacamento
        self.divisor(pdf, 8, ph - 37, pw - 8)

    def pagina_semanal_prioridades(self, pdf, x, y, w, h):
        accent = self._theme_accent()
        pdf.setFillColor(HexColor("#F8FAFC"))
        pdf.setStrokeColor(HexColor("#94A3B8"))
        pdf.setLineWidth(0.4)
        pdf.rect(sx(x * mm), sy(y * mm), sx(w * mm), sy(h * mm), fill=1, stroke=1)
        pdf.setFillColor(accent)
        pdf.rect(sx(x * mm), sy((y + h - 8) * mm), sx(w * mm), sy(8 * mm), fill=1, stroke=0)
        pdf.setFillColor(COR_GOLD)
        pdf.rect(sx(x * mm), sy((y + h - 8) * mm), sx(2 * mm), sy(8 * mm), fill=1, stroke=0)
        pdf.setFont(_FONT_B, 8)
        pdf.setFillColor(COR_HEADER_TXT)
        pdf.drawString(sx((x + 5) * mm), sy((y + h - 5.5) * mm), "PRIORIDADES DA SEMANA")
        yy = y + h - 14
        for _ in range(5):
            pdf.setStrokeColor(HexColor("#CBD5E1"))
            pdf.setLineWidth(0.2)
            pdf.rect(sx((x + 4) * mm), sy((yy - 1.2) * mm), sx(2.2 * mm), sy(2.2 * mm), stroke=1, fill=0)
            pdf.setFillColor(COR_GOLD)
            pdf.rect(sx((x + 4) * mm), sy((yy - 1.2) * mm), sx(0.3 * mm), sy(2.2 * mm), fill=1, stroke=0)
            pdf.setStrokeColor(HexColor("#E2E8F0"))
            pdf.line(sx((x + 8) * mm), sy((yy + 0.25) * mm), sx((x + w - 4) * mm), sy((yy + 0.25) * mm))
            yy -= 5

    def pagina_semanal_escrita(self, pdf, x, y, w, h):
        accent = self._theme_accent()
        pdf.setFillColor(HexColor("#F8FAFC"))
        pdf.setStrokeColor(HexColor("#94A3B8"))
        pdf.setLineWidth(0.4)
        pdf.rect(sx(x * mm), sy(y * mm), sx(w * mm), sy(h * mm), fill=1, stroke=1)
        pdf.setFillColor(accent)
        pdf.rect(sx(x * mm), sy((y + h - 8) * mm), sx(w * mm), sy(8 * mm), fill=1, stroke=0)
        pdf.setFillColor(COR_GOLD)
        pdf.rect(sx(x * mm), sy((y + h - 8) * mm), sx(2 * mm), sy(8 * mm), fill=1, stroke=0)
        pdf.setFont(_FONT_B, 8)
        pdf.setFillColor(COR_HEADER_TXT)
        pdf.drawString(sx((x + 5) * mm), sy((y + h - 5.5) * mm), localization.label("anotacoes"))
        yy = y + h - 14
        while yy >= y + 6:
            pdf.setStrokeColor(HexColor("#E2E8F0"))
            pdf.setLineWidth(0.15)
            pdf.line(sx((x + 4) * mm), sy(yy * mm), sx((x + w - 4) * mm), sy(yy * mm))
            yy -= 6

    def desenhar_logo(self, pdf):
        pass


estilo = Executivo()
