"""
Layouts da Agenda Juridica (template independente).
Reutiliza o estilo 'juridico' registrado em styles/manager.py.
"""

import calendar
from datetime import date, timedelta
from reportlab.lib.units import mm

import config
from config import sx, sy
import localization
from calendar_engine import obter_feriado


def _est():
    from styles.manager import obter_estilo
    return obter_estilo()


def pagina_dados(pdf):
    _est().pagina_dados(pdf)


def pagina_calendario_anual(pdf, ano):
    _est().pagina_calendario_anual(pdf, ano)


def pagina_mensal(pdf, data):
    _est().pagina_mensal(pdf, data)


def pagina_semanal(pdf, data_segunda):
    _est().pagina_semanal(pdf, data_segunda)


def pagina_diaria(pdf, data, com_agendamentos=False, maxima=None):
    _est().pagina_diaria(pdf, data, com_agendamentos=com_agendamentos, maxima=maxima)


def pagina_secao(pdf, titulo, colunas, num_linhas=22):
    _est().pagina_secao(pdf, titulo, colunas, num_linhas=num_linhas)


def pagina_maximas(pdf, maximas):
    _est().pagina_maximas(pdf, maximas)


SECOES = {
    "clientes": (
        "secao_clientes",
        [
            ("col_nome_empresa", 40),
            ("col_contato", 20),
            ("email", 22),
            ("col_oab_doc", 10),
            ("col_observacoes", 18),
        ],
    ),
    "processos": (
        "secao_processos",
        [
            ("col_numero", 16),
            ("col_partes", 26),
            ("col_area_tipo", 14),
            ("col_vara_tribunal", 18),
            ("col_status", 12),
            ("col_observacoes", 24),
        ],
    ),
    "honorarios": (
        "secao_honorarios",
        [
            ("col_data", 12),
            ("col_cliente", 24),
            ("col_servico", 26),
            ("col_valor", 16),
            ("col_pago", 8),
            ("col_observacoes", 24),
        ],
    ),
    "custas": (
        "secao_custas",
        [
            ("col_data", 12),
            ("col_descricao", 32),
            ("col_valor", 16),
            ("col_pago", 8),
            ("col_observacoes", 42),
        ],
    ),
    "protocolos": (
        "secao_protocolos",
        [
            ("col_data", 12),
            ("col_processo", 20),
            ("col_documento_peticao", 30),
            ("col_orgao", 20),
            ("col_observacoes", 28),
        ],
    ),
    "reunioes": (
        "secao_reunioes",
        [
            ("col_data", 12),
            ("col_horario", 10),
            ("col_cliente_parte", 24),
            ("col_pauta", 34),
            ("col_observacoes", 30),
        ],
    ),
}


def desenhar_secao(pdf, secao, paginas=2, num_linhas=22):
    if secao not in SECOES:
        return
    titulo_key, colunas_keys = SECOES[secao]
    titulo = localization.label(titulo_key)
    colunas = [(localization.label(k), w) for k, w in colunas_keys]
    for _ in range(paginas):
        pagina_secao(pdf, titulo, colunas, num_linhas=num_linhas)


def gerar_paginas_mensais(pdf, ano):
    for mes in range(1, 13):
        pagina_mensal(pdf, date(ano, mes, 1))


def gerar_paginas_semanais(pdf, ano):
    primeira = date(ano, 1, 1)
    pagina_semanal(pdf, primeira)
    proxima = primeira + timedelta(days=(7 - primeira.weekday()) % 7)
    if proxima == primeira:
        proxima += timedelta(days=7)
    while proxima.year == ano:
        pagina_semanal(pdf, proxima)
        proxima += timedelta(days=7)


def gerar_paginas_diarias(pdf, ano, com_agendamentos=False, incluir_maximas=True):
    from data.legal_maxims import obter_maxima_do_dia
    data = date(ano, 1, 1)
    dia_ano = 1
    while data.year == ano:
        maxima = obter_maxima_do_dia(dia_ano) if incluir_maximas else None
        pagina_diaria(pdf, data, com_agendamentos=com_agendamentos, maxima=maxima)
        data += timedelta(days=1)
        dia_ano += 1
