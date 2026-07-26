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
    nome="Minimalista",
    primaria="#FFFFFF",
    secundaria="#F8F8F8",
    destaque="#2D2D2D",
    texto="#2D2D2D",
    texto_secundario="#999999",
    linhas="#E0E0E0",
    bordas="#CCCCCC",
    cabecalho="#2D2D2D",
    texto_cabecalho="#FFFFFF",
    prioridade="#2D2D2D",
    mini_borda="#E0E0E0",
    mini_texto="#2D2D2D",
    mini_domingo="#C0392B",
    feriado="#C0392B",
    fonte_titulo="Helvetica-Bold",
    fonte_texto="Helvetica",
)

COR_LINHA_FINA = HexColor("#D5D5D5")
COR_TEXTO_SEC = HexColor("#999999")


class Minimalista(EstiloBase):
    nome = "Minimalista"

    def fundo_pagina(self, pdf):
        pdf.setFillColor(BRANCO)
        pdf.rect(0, 0, config.LARGURA, config.ALTURA, fill=1, stroke=0)

    def faixa_mes(self, pdf, x, y, w, h, data):
        accent = self._theme_accent()
        pdf.setFillColor(HexColor("#F0F0F0"))
        pdf.rect(sx(x * mm), sy(y * mm), sx(w * mm), sy(h * mm), fill=1, stroke=0)
        pdf.saveState()
        cx = sx((x + w / 2) * mm)
        cy = sy((y + h / 2) * mm)
        pdf.translate(cx, cy)
        pdf.rotate(90)
        pdf.setFont(_FONT_B, 9)
        pdf.setFillColor(accent)
        pdf.drawCentredString(0, 0, localization.nome_mes(data.month).upper())
        pdf.restoreState()

    def cabecalho_diario(self, pdf, data, x, y, w, h, is_2dpp=False, espelhar=False):
        accent = self._theme_accent()
        pdf.setFillColor(BRANCO)
        pdf.rect(sx(x * mm), sy(y * mm), sx(w * mm), sy(h * mm), fill=1, stroke=0)
        if is_2dpp:
            if espelhar:
                pdf.setFont(_FONT_B, 18)
                pdf.setFillColor(accent)
                pdf.drawRightString(sx((x + w - 3) * mm), sy((y + h - 9) * mm), data.strftime("%d"))
                pdf.setFont(_FONT_B, 10)
                pdf.setFillColor(HexColor("#555555"))
                pdf.drawRightString(sx((x + w - 3) * mm), sy((y + 11) * mm), localization.nome_dia(data).upper())
                pdf.setFont(_FONT, 7)
                pdf.setFillColor(COR_TEXTO_SEC)
                pdf.drawRightString(sx((x + w - 3) * mm), sy((y + 6) * mm), data.strftime("%d/%m/%Y"))
            else:
                pdf.setFont(_FONT_B, 18)
                pdf.setFillColor(accent)
                pdf.drawString(sx((x + 2) * mm), sy((y + h - 14) * mm), data.strftime("%d"))
                pdf.setFont(_FONT_B, 10)
                pdf.setFillColor(HexColor("#555555"))
                pdf.drawRightString(sx((x + w - 3) * mm), sy((y + 10) * mm), localization.nome_dia(data).upper())
                pdf.setFont(_FONT, 7)
                pdf.setFillColor(COR_TEXTO_SEC)
                pdf.drawRightString(sx((x + w - 3) * mm), sy((y + 3) * mm), data.strftime("%d/%m/%Y"))
        else:
            pdf.setFont(_FONT_B, 48)
            pdf.setFillColor(accent)
            pdf.drawRightString(sx((x + w - 3) * mm), sy((y + h - 5) * mm), data.strftime("%d"))
            pdf.setFont(_FONT_B, 11)
            pdf.setFillColor(HexColor("#555555"))
            pdf.drawRightString(sx((x + w - 3) * mm), sy((y + 10) * mm), localization.nome_dia(data).upper())
            pdf.setFont(_FONT, 7)
            pdf.setFillColor(COR_TEXTO_SEC)
            pdf.drawRightString(sx((x + w - 3) * mm), sy((y + 3) * mm), data.strftime("%d/%m/%Y"))
        pdf.setStrokeColor(COR_LINHA_FINA)
        pdf.setLineWidth(0.3)
        pdf.line(sx(x * mm), sy(y * mm), sx((x + w) * mm), sy(y * mm))

    def caixa_prioridades(self, pdf, x, y, w, h):
        accent = self._theme_accent()
        task = self._theme_tasks()
        pdf.setFillColor(BRANCO)
        pdf.setStrokeColor(COR_LINHA_FINA)
        pdf.setLineWidth(0.4)
        pdf.rect(sx(x * mm), sy(y * mm), sx(w * mm), sy(h * mm), fill=1, stroke=1)
        pdf.setFont(_FONT_B, 7)
        pdf.setFillColor(accent)
        pdf.drawString(sx((x + 4) * mm), sy((y + h - 8) * mm), "PRIORIDADES")
        pdf.setStrokeColor(COR_LINHA_FINA)
        pdf.setLineWidth(0.25)
        pdf.line(sx((x + 4) * mm), sy((y + h - 10) * mm), sx((x + w - 4) * mm), sy((y + h - 10) * mm))
        espacamento = (h - 14) / 4
        yy = y + h - 14
        dot_colors = [HexColor("#8D8D8D"), HexColor("#AAAAAA"), HexColor("#C0C0C0"), HexColor("#D8D8D8")]
        for cor in dot_colors:
            pdf.setFillColor(task if cor == dot_colors[0] else cor)
            pdf.circle(sx((x + 7) * mm), sy(yy * mm), 0.8 * mm, fill=1, stroke=0)
            pdf.setStrokeColor(COR_LINHA_FINA)
            pdf.setLineWidth(0.2)
            pdf.line(sx((x + 10) * mm), sy(yy * mm), sx((x + w - 4) * mm), sy(yy * mm))
            yy -= espacamento

    def area_anotacoes(self, pdf, x, y, w, h, num_linhas=8):
        pdf.setFillColor(BRANCO)
        pdf.setStrokeColor(COR_LINHA_FINA)
        pdf.setLineWidth(0.3)
        pdf.rect(sx(x * mm), sy(y * mm), sx(w * mm), sy(h * mm), fill=1, stroke=1)
        espacamento = h / (num_linhas + 1)
        yy = y + h - espacamento
        for _ in range(num_linhas):
            pdf.setStrokeColor(COR_LINHA_FINA)
            pdf.setLineWidth(0.2)
            pdf.line(sx((x + 3) * mm), sy(yy * mm), sx((x + w - 3) * mm), sy(yy * mm))
            yy -= espacamento

    def divisor(self, pdf, x1, y, x2):
        pdf.setStrokeColor(COR_LINHA_FINA)
        pdf.setLineWidth(0.25)
        pdf.line(sx(x1 * mm), sy(y * mm), sx(x2 * mm), sy(y * mm))

    def decorar_canto(self, pdf, x, y, corner="tl"):
        pass

    def decorar_borda(self, pdf):
        pass

    def pagina_dados_pessoais(self, pdf, campos, logo_bytes=None):
        accent = self._theme_accent()
        pdf.setFillColor(BRANCO)
        pdf.rect(0, 0, config.LARGURA, config.ALTURA, fill=1, stroke=0)
        pw = config.LARGURA / mm
        ph = config.ALTURA / mm
        pdf.setFont(_FONT_B, 18)
        pdf.setFillColor(accent)
        pdf.drawCentredString(sx(pw / 2 * mm), sy((ph - 20) * mm), "DADOS PESSOAIS")
        pdf.setStrokeColor(COR_LINHA_FINA)
        pdf.setLineWidth(0.3)
        pdf.line(sx((pw / 2 - 30) * mm), sy((ph - 25) * mm), sx((pw / 2 + 30) * mm), sy((ph - 25) * mm))
        yy = ph - 40
        for campo in campos:
            pdf.setFont(_FONT_B, 9)
            pdf.setFillColor(HexColor("#666666"))
            pdf.drawString(sx(20 * mm), sy(yy * mm), campo)
            pdf.setStrokeColor(COR_LINHA_FINA)
            pdf.setLineWidth(0.25)
            pdf.line(sx(20 * mm), sy((yy - 2) * mm), sx((pw - 20) * mm), sy((yy - 2) * mm))
            yy -= 18
        if logo_bytes:
            logo_bytes.seek(0)
            try:
                from reportlab.lib.utils import ImageReader
                img = ImageReader(logo_bytes)
                iw, ih = img.getSize()
                ratio = min(50 / iw, 25 / ih)
                pdf.drawImage(img, sx(85 * mm), sy(210 * mm), width=sx(iw * ratio * mm), height=sy(ih * ratio * mm), mask='auto')
            except Exception:
                pass
        pdf.showPage()

    def planejamento(self, pdf, caixas):
        accent = self._theme_accent()
        pdf.setFillColor(BRANCO)
        pdf.rect(0, 0, config.LARGURA, config.ALTURA, fill=1, stroke=0)
        pw = config.LARGURA / mm
        ph = config.ALTURA / mm
        pdf.setFont(_FONT_B, 18)
        pdf.setFillColor(accent)
        pdf.drawCentredString(sx(pw / 2 * mm), sy((ph - 18) * mm), "PLANEJAMENTO ANUAL")
        pdf.setFont(_FONT, 8)
        pdf.setFillColor(COR_TEXTO_SEC)
        pdf.drawCentredString(sx(pw / 2 * mm), sy((ph - 26) * mm), "Metas e Objetivos")
        pdf.setStrokeColor(COR_LINHA_FINA)
        pdf.setLineWidth(0.3)
        pdf.line(sx((pw / 2 - 35) * mm), sy((ph - 30) * mm), sx((pw / 2 + 35) * mm), sy((ph - 30) * mm))
        for titulo, y, alt in caixas:
            pdf.setFillColor(BRANCO)
            pdf.setStrokeColor(COR_LINHA_FINA)
            pdf.setLineWidth(0.3)
            pdf.rect(sx(15 * mm), sy(y * mm), sx(118 * mm), sy(alt * mm), fill=1, stroke=1)
            pdf.setFont(_FONT_B, 7)
            pdf.setFillColor(accent)
            pdf.drawString(sx(19 * mm), sy((y + alt - 8) * mm), titulo.upper())
            yy = y + alt - 12
            while yy >= y + 4:
                pdf.setStrokeColor(COR_LINHA_FINA)
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
        pdf.setFillColor(HexColor("#F0F0F0"))
        pdf.rect(sx(8 * mm), sy((ph - 14) * mm), sx((pw - 16) * mm), sy(8 * mm), fill=1, stroke=0)
        pdf.setFont(_FONT_B, 10)
        pdf.setFillColor(accent)
        pdf.drawCentredString(sx(pw / 2 * mm), sy((ph - 10) * mm), "PLANEJAMENTO SEMANAL")

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
            pdf.setFillColor(HexColor("#FAFAFA"))
            pdf.rect(sx(x * mm), sy(y * mm), sx(largura * mm), sy(altura * mm), fill=1, stroke=0)
            pdf.setStrokeColor(COR_LINHA_FINA)
            pdf.setLineWidth(0.3)
            pdf.rect(sx(x * mm), sy(y * mm), sx(largura * mm), sy(altura * mm), fill=0, stroke=1)
            pdf.setFont(_FONT_B, 7)
            pdf.setFillColor(accent)
            pdf.drawCentredString(sx((x + largura / 2) * mm), sy((y + 2.5) * mm), texto)
            pdf.setStrokeColor(COR_LINHA_FINA)
            pdf.setLineWidth(0.2)
            pdf.circle(sx((x + largura / 2) * mm), sy((y - 4) * mm), 1.0 * mm, stroke=1, fill=0)
            x += largura + espacamento
        self.divisor(pdf, 8, ph - 37, pw - 8)

    def pagina_semanal_prioridades(self, pdf, x, y, w, h):
        accent = self._theme_accent()
        pdf.setFillColor(BRANCO)
        pdf.setStrokeColor(COR_LINHA_FINA)
        pdf.setLineWidth(0.35)
        pdf.rect(sx(x * mm), sy(y * mm), sx(w * mm), sy(h * mm), fill=1, stroke=1)
        pdf.setFont(_FONT_B, 8)
        pdf.setFillColor(accent)
        pdf.drawString(sx((x + 4) * mm), sy((y + h - 8) * mm), "PRIORIDADES DA SEMANA")
        pdf.setStrokeColor(COR_LINHA_FINA)
        pdf.setLineWidth(0.2)
        pdf.line(sx((x + 4) * mm), sy((y + h - 10) * mm), sx((x + w - 4) * mm), sy((y + h - 10) * mm))
        yy = y + h - 16
        for _ in range(5):
            pdf.setStrokeColor(COR_LINHA_FINA)
            pdf.setLineWidth(0.2)
            pdf.rect(sx((x + 4) * mm), sy((yy - 1.2) * mm), sx(2.2 * mm), sy(2.2 * mm), stroke=1, fill=0)
            pdf.line(sx((x + 8) * mm), sy((yy + 0.25) * mm), sx((x + w - 4) * mm), sy((yy + 0.25) * mm))
            yy -= 5

    def pagina_semanal_escrita(self, pdf, x, y, w, h):
        accent = self._theme_accent()
        pdf.setFillColor(BRANCO)
        pdf.setStrokeColor(COR_LINHA_FINA)
        pdf.setLineWidth(0.35)
        pdf.rect(sx(x * mm), sy(y * mm), sx(w * mm), sy(h * mm), fill=1, stroke=1)
        pdf.setFont(_FONT_B, 8)
        pdf.setFillColor(accent)
        pdf.drawString(sx((x + 4) * mm), sy((y + h - 8) * mm), "ANOTACOES")
        pdf.setStrokeColor(COR_LINHA_FINA)
        pdf.setLineWidth(0.2)
        pdf.line(sx((x + 4) * mm), sy((y + h - 10) * mm), sx((x + w - 4) * mm), sy((y + h - 10) * mm))
        yy = y + h - 16
        while yy >= y + 6:
            pdf.setStrokeColor(COR_LINHA_FINA)
            pdf.setLineWidth(0.15)
            pdf.line(sx((x + 4) * mm), sy(yy * mm), sx((x + w - 4) * mm), sy(yy * mm))
            yy -= 6

    def desenhar_logo(self, pdf):
        pass


estilo = Minimalista()
