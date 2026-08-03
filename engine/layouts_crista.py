"""
Layouts da Agenda Crista (template independente).
Reutiliza o estilo 'crista' registrado em styles/manager.py.
Paginas iniciais iguais as da agenda datada: dados pessoais, calendario anual e planejamento.
"""

from datetime import date, timedelta

import config
import layouts_a5


def _est():
    from styles.manager import obter_estilo
    return obter_estilo()


def pagina_dados(pdf):
    layouts_a5.pagina_dados_pessoais(pdf)


def pagina_calendario_anual(pdf, ano):
    _est().pagina_calendario_anual(pdf, ano)


def pagina_planejamento(pdf):
    layouts_a5.pagina_planejamento(pdf)


def pagina_diaria(pdf, data, com_agendamentos=False):
    _est().pagina_diaria(pdf, data, com_agendamentos=com_agendamentos)


def gerar_paginas_diarias(pdf, ano, com_agendamentos=False):
    data = date(ano, 1, 1)
    while data.year == ano:
        pagina_diaria(pdf, data, com_agendamentos=com_agendamentos)
        data += timedelta(days=1)


def gerar_paginas_iniciais(pdf, ano):
    """Paginas iniciais identicas a agenda datada."""
    layouts_a5.pagina_dados_pessoais(pdf)
    layouts_a5.pagina_calendario_anual(pdf, ano)
    layouts_a5.pagina_planejamento(pdf)
