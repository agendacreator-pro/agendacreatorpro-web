from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
import os

import config
from config import sx, sy
from colors import *
from calendar_engine import *
import themes


_logo_cache = None
_FONT_B = "Helvetica-Bold"
_FONT = "Helvetica"


def escrever(pdf, texto, x, y, tamanho=None, negrito=False, cor=None):
    if cor is None:
        cor = PRETO
    pdf.setFillColor(cor)
    pdf.setFont(_FONT_B if negrito else _FONT, tamanho or config.NORMAL)
    pdf.drawString(sx(x * mm), sy(y * mm), str(texto))


def escrever_centro(pdf, texto, x, y, tamanho=None, negrito=False, cor=None):
    if cor is None:
        cor = PRETO
    pdf.setFillColor(cor)
    pdf.setFont(_FONT_B if negrito else _FONT, tamanho or config.NORMAL)
    pdf.drawCentredString(sx(x * mm), sy(y * mm), str(texto))


def linha(pdf, x1, y1, x2, y2, cor=None):
    if cor is None:
        cor = LINHA
    pdf.setStrokeColor(cor)
    pdf.setLineWidth(0.35)
    pdf.line(sx(x1 * mm), sy(y1 * mm), sx(x2 * mm), sy(y2 * mm))


def circulo(pdf, x, y, raio, cor):
    pdf.setFillColor(cor)
    pdf.circle(sx(x * mm), sy(y * mm), raio * mm, fill=1, stroke=0)


def caixa(pdf, x, y, largura, altura, cor=None):
    if cor is None:
        cor = BRANCO
    pdf.setFillColor(cor)
    pdf.roundRect(sx(x * mm), sy(y * mm), sx(largura * mm), sy(altura * mm), 3 * mm, fill=1, stroke=1)


def card(pdf, x, y, largura, altura, titulo="", cor=None):
    if cor is None:
        cor = themes.tema_atual.tarefas
    pdf.setFillColor(cor)
    pdf.setStrokeColor(themes.tema_atual.linhas)
    pdf.setLineWidth(0.4)
    pdf.roundRect(sx(x * mm), sy(y * mm), sx(largura * mm), sy(altura * mm), 3 * mm, fill=1, stroke=1)
    if titulo != "":
        pdf.setFillColor(themes.tema_atual.titulo)
        pdf.roundRect(sx(x * mm), sy((y + altura - 7) * mm), sx(largura * mm), sy(7 * mm), 3 * mm, fill=1, stroke=0)
        pdf.setFillColor(PRETO)
        pdf.setFont(_FONT_B, 8)
        pdf.drawCentredString(sx((x + largura / 2) * mm), sy((y + altura - 5) * mm), titulo.upper())


def desenhar_logo(pdf):
    global _logo_cache
    caminho = os.path.join("assets", "logo_meell.png")
    if os.path.exists(caminho):
        if _logo_cache is None:
            _logo_cache = ImageReader(caminho)
        pdf.drawImage(
            _logo_cache, sx(102 * mm), sy(186 * mm),
            width=sx(70 * mm), height=sy(25 * mm),
            preserveAspectRatio=True, mask="auto"
        )


def desenhar_rodape(pdf):
    pass
