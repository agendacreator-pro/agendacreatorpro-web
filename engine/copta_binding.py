"""
Encadernacao Copta: imposicao de paginas em cadernos (signatures)
para impressao 2-up em A4 paisagem, frente e verso.

Nao altera layouts existentes - apenas processa o PDF gerado
rearranjando as paginas na ordem correta de caderno.
"""

import math
from io import BytesIO
from reportlab.lib.units import mm
from reportlab.lib.pagesizes import A4
from pypdf import PdfWriter, PdfReader, Transformation

import config
from config import sx, sy
import themes
from themes import definir
import layouts_a5
import layouts_permanente_a5
from pdf_generator import gerar_pdf_permanente, gerar_pdf_datada, gerar_preview


FOLHAS_POR_CADERNO = 5  # 5 folhas = 20 paginas por caderno


def _ordem_caderno(total_paginas, folhas_por_caderno=5):
    """
    Gera a sequencia de indices de pagina no formato de imposicao
    para cadernos (signatures), 2-up frente e verso.

    Para um caderno de N paginas (múltiplo de 4):
      Folha s, frente: [N-2*s, 2*s+1]
      Folha s, verso:  [2*s+2, N-2*s-1]

    Retorna lista de (idx_esquerda, idx_direita) para cada folha.
    """
    pag_por_caderno = folhas_por_caderno * 4
    num_cadernos = math.ceil(total_paginas / pag_por_caderno)
    total_completado = num_cadernos * pag_por_caderno
    folhas = []
    for caderno in range(num_cadernos):
        inicio = caderno * pag_por_caderno
        ultima = inicio + pag_por_caderno - 1
        for folha in range(folhas_por_caderno):
            # frente: [ultima-2s, inicio+2s]
            folhas.append((ultima - 2 * folha, inicio + 2 * folha))
            # verso: [inicio+2s+1, ultima-2s-1]
            folhas.append((inicio + 2 * folha + 1, ultima - 2 * folha - 1))
    return folhas, total_completado


def impor_cadernos(buffer_entrada, folhas_por_caderno=5):
    """
    Le um PDF de paginas A5 e rearranja em cadernos (signatures)
    no formato 2-up em A4 paisagem, pronto para impressao frente e verso.

    Args:
        buffer_entrada: BytesIO com PDF de paginas A5 avulsas
        folhas_por_caderno: num de folhas por caderno (5 = 20 pag)

    Returns:
        BytesIO com PDF imposto (2-up A4 paisagem)
    """
    reader = PdfReader(buffer_entrada)
    paginas = list(reader.pages)
    total = len(paginas)

    ordem, total_completado = _ordem_caderno(total, folhas_por_caderno)

    # adiciona paginas em branco se necessario
    if total_completado > total:
        writer_pad = PdfWriter()
        for p in paginas:
            writer_pad.add_page(p)
        for _ in range(total_completado - total):
            writer_pad.add_blank_page(148 * mm, 210 * mm)
        buf_pad = BytesIO()
        writer_pad.write(buf_pad)
        buf_pad.seek(0)
        reader = PdfReader(buf_pad)
        paginas = list(reader.pages)

    # dimensoes
    a4_w = 297 * mm
    a4_h = 210 * mm
    a5_w = 148 * mm
    a5_h = 210 * mm

    writer = PdfWriter()
    # cada par na ordem = uma folha A4 frente+verso
    for i in range(0, len(ordem), 2):
        if i + 1 >= len(ordem):
            break

        # --- FRENTE ---
        page_front = writer.add_blank_page(a4_w, a4_h)
        idx_esq, idx_dir = ordem[i]
        if idx_esq < len(paginas):
            page_front.merge_translated_page(paginas[idx_esq], 0, 0)
        if idx_dir < len(paginas):
            page_front.merge_translated_page(paginas[idx_dir], a5_w, 0)

        # --- VERSO ---
        page_back = writer.add_blank_page(a4_w, a4_h)
        idx_esq, idx_dir = ordem[i + 1]
        if idx_esq < len(paginas):
            page_back.merge_translated_page(paginas[idx_esq], 0, 0)
        if idx_dir < len(paginas):
            page_back.merge_translated_page(paginas[idx_dir], a5_w, 0)

    saida = BytesIO()
    writer.write(saida)
    saida.seek(0)
    return saida


def gerar_pdf_permanente_copta(quantidade_paginas, tema, ano, formato="A5", com_agendamentos=False):
    """Gera PDF permanente com imposicao copta."""
    buf = gerar_pdf_permanente(
        quantidade_paginas, tema, ano, formato=formato,
        com_agendamentos=com_agendamentos
    )
    return impor_cadernos(buf, FOLHAS_POR_CADERNO)


def gerar_pdf_datada_copta(ano, tema, layout_pagina="1", formato="A5", com_agendamentos=False):
    """Gera PDF datado com imposicao copta."""
    buf = gerar_pdf_datada(
        ano, tema, layout_pagina=layout_pagina, formato=formato,
        com_agendamentos=com_agendamentos
    )
    return impor_cadernos(buf, FOLHAS_POR_CADERNO)


def gerar_preview_copta(ano, tema, layout_pagina="1", formato="A5", com_agendamentos=False):
    """Preview sem imposicao (apenas primeiras paginas A5 avulsas)."""
    return gerar_preview(
        ano, tema, layout_pagina=layout_pagina, formato=formato,
        com_agendamentos=com_agendamentos
    )
