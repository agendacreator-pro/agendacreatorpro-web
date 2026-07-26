from layouts_base import *
import config
from config import sx, sy
import calendar
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'styles'))
from styles.manager import obter_estilo
import themes

_FONT_B = config.FONTE_NEGRITO
_FONT = config.FONTE


def _est():
    return obter_estilo()


def _tema():
    return themes.tema_atual


def pagina_dados_pessoais(pdf):
    est = _est()
    campos = [
        "Nome", "Telefone", "E-mail", "Endereco",
        "Cidade", "CEP", "Contato de Emergencia",
        "Telefone de Emergencia"
    ]
    est.pagina_dados_pessoais(pdf, campos)


def pagina_planejamento(pdf):
    est = _est()
    caixas = [
        ("Metas", 168, 24),
        ("Projetos", 140, 24),
        ("Financeiro", 112, 24),
        ("Saude", 84, 24),
        ("Estudos", 56, 24),
        ("Viagens", 28, 24),
    ]
    est.planejamento(pdf, caixas)


def desenhar_cabecalho(pdf, data):
    est = _est()
    est.faixa_mes(pdf, 10, 166, 10, 30, data)
    est.cabecalho_diario(pdf, data, 22, 166, 100, 30)


def desenhar_caixa_prioridades(pdf):
    est = _est()
    est.caixa_prioridades(pdf, 15, 132, 118, 28)


def desenhar_area_anotacoes(pdf):
    est = _est()
    est.area_anotacoes(pdf, 15, 6, 118, 122, num_linhas=20)


def desenhar_pagina(pdf, data):
    est = _est()
    est.fundo_pagina(pdf)
    desenhar_cabecalho(pdf, data)
    desenhar_caixa_prioridades(pdf)
    desenhar_area_anotacoes(pdf)
    feriado = obter_feriado(data)
    if feriado:
        pdf.setFont(_FONT, 8)
        pdf.setFillColor(_tema().destaque)
        pdf.drawString(18 * mm, 162 * mm, feriado)
    pdf.showPage()


def _metade_2dpp(pdf, data, base_y_mm, alt_mm, espelhar=False):
    est = _est()
    pw_mm = config.LARGURA / mm

    margin_l = 8
    margin_r = pw_mm - 8
    content_w = margin_r - margin_l

    if espelhar:
        strip_x = margin_r - 14
        strip_w = 10
        header_x = margin_l
        header_w = content_w - 40
    else:
        strip_x = margin_l
        strip_w = 10
        header_x = margin_l + 16
        header_w = content_w - 16

    top_pad = alt_mm * 0.03
    bottom_pad = alt_mm * 0.03
    usable_h = alt_mm - top_pad - bottom_pad

    header_h = usable_h * 0.22
    header_y = base_y_mm + alt_mm - top_pad - header_h

    strip_h = header_h
    strip_y = header_y

    prior_h = usable_h * 0.30
    prior_y = header_y - usable_h * 0.02 - prior_h

    notes_h = prior_y - (base_y_mm + bottom_pad)
    notes_y = base_y_mm + bottom_pad

    est.faixa_mes(pdf, strip_x, strip_y, strip_w, strip_h, data)
    est.cabecalho_diario(pdf, data, header_x, header_y, header_w, header_h, is_2dpp=True, espelhar=espelhar)

    cx = margin_l
    est.caixa_prioridades(pdf, cx, prior_y, content_w, prior_h)
    est.area_anotacoes(pdf, cx, notes_y, content_w, notes_h, num_linhas=max(3, int(notes_h / 5)))


def desenhar_pagina_2dias(pdf, data1, data2):
    est = _est()
    est.fundo_pagina(pdf)

    alt_mm = config.ALTURA / mm / 2

    _metade_2dpp(pdf, data1, alt_mm, alt_mm, espelhar=False)
    if data2 is not None:
        _metade_2dpp(pdf, data2, 0, alt_mm, espelhar=True)

    est.divisor(pdf, 0, alt_mm, config.LARGURA / mm)

    feriado = obter_feriado(data1)
    if feriado:
        pdf.setFont(_FONT, 7)
        pdf.setFillColor(_tema().destaque)
        pdf.drawString(10 * mm, (alt_mm - 3) * mm, feriado)
    if data2 is not None:
        feriado = obter_feriado(data2)
        if feriado:
            pdf.setFont(_FONT, 7)
            pdf.setFillColor(_tema().destaque)
            pdf.drawString(10 * mm, 3 * mm, feriado)

    pdf.showPage()
