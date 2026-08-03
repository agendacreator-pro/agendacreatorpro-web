"""
Encadernacao Copta: paginas A5 agrupadas duas a duas, lado a lado,
em folhas A4 paisagem, na ordem sequencial (1-2, 3-4, 5-6, ...).
Ao dobrar cada folha ao meio e costurar na lombada, a ordem fica correta.
Preview comeca de 1o de janeiro.
"""

from io import BytesIO
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from pypdf import PdfReader, PdfWriter

import config
from config import sx, sy
import themes
from themes import definir
import layouts_a5
from datetime import date

from pdf_generator import gerar_pdf_permanente, gerar_pdf_datada, gerar_preview
from pdf_generator import gerar_pdf_juridica, gerar_preview_juridica
from pdf_generator import gerar_pdf_crista, gerar_preview_crista


A5_LARGURA = 148 * mm
A5_ALTURA = 210 * mm
FOLHA_LARGURA = 297 * mm
FOLHA_ALTURA = 210 * mm


def _montar_cadernilha(buf):
    """Junta as paginas A5 duas a duas em folhas A4 paisagem (ordem sequencial)."""
    reader = PdfReader(buf)
    writer = PdfWriter()
    paginas = reader.pages
    for i in range(0, len(paginas), 2):
        folha = writer.add_blank_page(FOLHA_LARGURA, FOLHA_ALTURA)
        folha.merge_translated_page(paginas[i], 0, 0)
        if i + 1 < len(paginas):
            folha.merge_translated_page(paginas[i + 1], A5_LARGURA, 0)
    out = BytesIO()
    writer.write(out)
    out.seek(0)
    return out


def gerar_pdf_juridica_copta(ano, tema, formato="A5", com_agendamentos=False,
                             incluir_maximas=True, incluir_anual=True,
                             incluir_mensais=True, incluir_semanais=True,
                             incluir_diarias=True, secoes=None, secoes_paginas=2):
    buf = gerar_pdf_juridica(ano, tema, formato=formato,
                             com_agendamentos=com_agendamentos,
                             incluir_maximas=incluir_maximas,
                             incluir_anual=incluir_anual,
                             incluir_mensais=incluir_mensais,
                             incluir_semanais=incluir_semanais,
                             incluir_diarias=incluir_diarias,
                             secoes=secoes, secoes_paginas=secoes_paginas)
    return _montar_cadernilha(buf)


def gerar_preview_juridica_copta(ano, tema, formato="A5", com_agendamentos=False,
                                 incluir_maximas=True, secoes=None):
    buf = gerar_preview_juridica(ano, tema, formato=formato,
                                 com_agendamentos=com_agendamentos,
                                 incluir_maximas=incluir_maximas,
                                 secoes=secoes)
    return _montar_cadernilha(buf)


def gerar_pdf_crista_copta(ano, tema, formato="A5", com_agendamentos=False,
                           layout_pagina="1"):
    buf = gerar_pdf_crista(ano, tema, formato=formato,
                           com_agendamentos=com_agendamentos,
                           layout_pagina=layout_pagina)
    return _montar_cadernilha(buf)


def gerar_preview_crista_copta(ano, tema, formato="A5", com_agendamentos=False,
                               layout_pagina="1"):
    buf = gerar_preview_crista(ano, tema, formato=formato,
                               com_agendamentos=com_agendamentos,
                               layout_pagina=layout_pagina)
    return _montar_cadernilha(buf)


def gerar_pdf_permanente_copta(quantidade_paginas, tema, ano, formato="A5", com_agendamentos=False):
    buf = gerar_pdf_permanente(quantidade_paginas, tema, ano, formato, com_agendamentos=com_agendamentos)
    return _montar_cadernilha(buf)


def gerar_pdf_datada_copta(ano, tema, layout_pagina="1", formato="A5", com_agendamentos=False):
    buf = gerar_pdf_datada(ano, tema, layout_pagina, formato, com_agendamentos=com_agendamentos)
    return _montar_cadernilha(buf)


def gerar_preview_copta(ano, tema, layout_pagina="1", formato="A5", com_agendamentos=False):
    definir(tema)
    config.LARGURA, config.ALTURA = config.obter_tamanho_pagina(formato)
    config.FORMATO = formato.upper()
    config.AREA_UTIL = config.LARGURA - config.MARGEM_ESQ - config.MARGEM_DIR
    config.atualizar_escala()

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=(config.LARGURA, config.ALTURA))
    pdf.setPageCompression(0)

    layouts_a5.pagina_dados_pessoais(pdf)
    layouts_a5.pagina_calendario_anual(pdf, ano)
    layouts_a5.pagina_planejamento(pdf)

    data = date(ano, 1, 1)
    if layout_pagina == "1":
        layouts_a5.desenhar_pagina(pdf, data, com_agendamentos=com_agendamentos)
    else:
        layouts_a5.desenhar_pagina_2dias(pdf, data, date(ano, 1, 2), com_agendamentos=com_agendamentos)

    pdf.save()
    buffer.seek(0)
    return _montar_cadernilha(buffer)
