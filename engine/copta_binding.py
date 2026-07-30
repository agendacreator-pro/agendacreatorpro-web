"""
Encadernacao Copta: margem de lombada extra + paginas em ordem sequencial.
Usa os geradores existentes e pos-processa com pypdf para deslocar
o conteudo 2mm a direita (margem esquerda = 10mm).
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


DESLOCAMENTO = 2  # mm extras na lombada


def _aplicar_lombada(buf):
    """Desloca todo o conteudo DESLOCAMENTO mm a direita."""
    reader = PdfReader(buf)
    writer = PdfWriter()
    a5_w = 148 * mm
    a5_h = 210 * mm
    for page in reader.pages:
        np = writer.add_blank_page(a5_w, a5_h)
        np.merge_translated_page(page, DESLOCAMENTO * mm, 0)
    out = BytesIO()
    writer.write(out)
    out.seek(0)
    return out


def gerar_pdf_permanente_copta(quantidade_paginas, tema, ano, formato="A5", com_agendamentos=False):
    buf = gerar_pdf_permanente(quantidade_paginas, tema, ano, formato, com_agendamentos=com_agendamentos)
    return _aplicar_lombada(buf)


def gerar_pdf_datada_copta(ano, tema, layout_pagina="1", formato="A5", com_agendamentos=False):
    buf = gerar_pdf_datada(ano, tema, layout_pagina, formato, com_agendamentos=com_agendamentos)
    return _aplicar_lombada(buf)


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
    return buffer
