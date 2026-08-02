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
import layouts_juridica


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


def gerar_pdf_juridica(ano, tema, formato="A5", com_agendamentos=False,
                       incluir_maximas=True, incluir_anual=True,
                       incluir_mensais=True, incluir_semanais=True,
                       incluir_diarias=True, secoes=None, secoes_paginas=2,
                       preview=False):
    """Gera a Agenda Juridica. Se preview=True, gera apenas paginas de exemplo."""
    from styles.manager import definir as definir_estilo
    definir_estilo('juridico')
    definir(tema)
    config.LARGURA, config.ALTURA = config.obter_tamanho_pagina(formato)
    config.FORMATO = formato.upper()
    config.AREA_UTIL = config.LARGURA - config.MARGEM_ESQ - config.MARGEM_DIR
    config.ESCALA_X = 1.0
    config.ESCALA_Y = 1.0

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=(config.LARGURA, config.ALTURA))
    pdf.setPageCompression(0)

    layouts_juridica.pagina_dados(pdf)

    if preview:
        layouts_juridica.pagina_calendario_anual(pdf, ano)
        layouts_juridica.pagina_mensal(pdf, date(ano, 1, 1))
        layouts_juridica.pagina_semanal(pdf, date(ano, 1, 1))
        from data.legal_maxims import obter_maximas, obter_maxima_do_dia
        preview_maxima = obter_maxima_do_dia(15) if incluir_maximas else None
        layouts_juridica.pagina_diaria(pdf, date(ano, 1, 15),
                                       com_agendamentos=com_agendamentos,
                                       maxima=preview_maxima)
        layouts_juridica.pagina_maximas(pdf, obter_maximas()[:22])
        if secoes:
            for secao in secoes:
                layouts_juridica.desenhar_secao(pdf, secao, paginas=1, num_linhas=22)
        pdf.save()
        buffer.seek(0)
        return buffer

    if incluir_anual:
        layouts_juridica.pagina_calendario_anual(pdf, ano)
    if incluir_mensais:
        layouts_juridica.gerar_paginas_mensais(pdf, ano)
    if incluir_semanais:
        layouts_juridica.gerar_paginas_semanais(pdf, ano)
    if incluir_diarias:
        layouts_juridica.gerar_paginas_diarias(pdf, ano,
                                               com_agendamentos=com_agendamentos,
                                               incluir_maximas=incluir_maximas)
    if secoes:
        for secao in secoes:
            layouts_juridica.desenhar_secao(pdf, secao, paginas=secoes_paginas)

    if incluir_maximas:
        from data.legal_maxims import obter_maximas
        todas = obter_maximas()
        passo = 20
        for i in range(0, len(todas), passo):
            layouts_juridica.pagina_maximas(pdf, todas[i:i + passo])

    pdf.save()
    buffer.seek(0)
    return buffer


def gerar_preview_juridica(ano, tema, formato="A5", com_agendamentos=False,
                           incluir_maximas=True, secoes=None):
    return gerar_pdf_juridica(ano, tema, formato=formato,
                              com_agendamentos=com_agendamentos,
                              incluir_maximas=incluir_maximas,
                              secoes=secoes,
                              preview=True)
