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
        "REGISTRO DE CLIENTES",
        [
            ("NOME / EMPRESA", 40),
            ("CONTATO", 20),
            ("E-MAIL", 22),
            ("OAB / DOC", 10),
            ("OBSERVACOES", 18),
        ],
    ),
    "processos": (
        "CONTROLE DE PROCESSOS",
        [
            ("NUMERO", 16),
            ("PARTES", 26),
            ("AREA / TIPO", 14),
            ("VARA / TRIBUNAL", 18),
            ("STATUS", 12),
            ("OBSERVACOES", 24),
        ],
    ),
    "honorarios": (
        "REGISTRO DE HONORARIOS",
        [
            ("DATA", 12),
            ("CLIENTE", 24),
            ("SERVICO", 26),
            ("VALOR", 16),
            ("PAGO", 8),
            ("OBSERVACOES", 24),
        ],
    ),
    "custas": (
        "REGISTRO DE CUSTAS E DESPESAS",
        [
            ("DATA", 12),
            ("DESCRICAO", 32),
            ("VALOR", 16),
            ("PAGO", 8),
            ("OBSERVACOES", 42),
        ],
    ),
    "protocolos": (
        "REGISTRO DE PROTOCOLOS",
        [
            ("DATA", 12),
            ("PROCESSO", 20),
            ("DOCUMENTO / PETICAO", 30),
            ("ORGAO", 20),
            ("OBSERVACOES", 28),
        ],
    ),
    "reunioes": (
        "REGISTRO DE REUNIOES",
        [
            ("DATA", 12),
            ("HORARIO", 10),
            ("CLIENTE / PARTE", 24),
            ("PAUTA", 34),
            ("OBSERVACOES", 30),
        ],
    ),
}


def desenhar_secao(pdf, secao, paginas=2, num_linhas=22):
    if secao not in SECOES:
        return
    titulo, colunas = SECOES[secao]
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
