from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from datetime import date, timedelta

import config
from config import sx, sy
import themes
from themes import definir
import layouts_a5
import layouts_permanente_a5


def gerar_pdf_permanente(quantidade_paginas, tema, ano, formato="A5", com_agendamentos=False):
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

    for _ in range(quantidade_paginas):
        layouts_permanente_a5.desenhar_pagina_semanal(pdf, com_agendamentos=com_agendamentos)

    pdf.save()
    buffer.seek(0)
    return buffer


def gerar_pdf_datada(ano, tema, layout_pagina="1", formato="A5", com_agendamentos=False):
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
        while data.year == ano:
            layouts_a5.desenhar_pagina(pdf, data, com_agendamentos=com_agendamentos)
            data += timedelta(days=1)
    else:
        while data.year == ano:
            data1 = data
            data2 = data + timedelta(days=1)
            if data2.year != ano:
                data2 = None
            layouts_a5.desenhar_pagina_2dias(pdf, data1, data2, com_agendamentos=com_agendamentos)
            data += timedelta(days=2)

    pdf.save()
    buffer.seek(0)
    return buffer


def gerar_preview(ano, tema, layout_pagina="1", formato="A5", com_agendamentos=False):
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

    data = date(ano, 1, 15)
    if layout_pagina == "1":
        layouts_a5.desenhar_pagina(pdf, data, com_agendamentos=com_agendamentos)
    else:
        layouts_a5.desenhar_pagina_2dias(pdf, data, date(ano, 1, 16), com_agendamentos=com_agendamentos)

    pdf.save()
    buffer.seek(0)
    return buffer
