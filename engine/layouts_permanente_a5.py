from reportlab.lib.units import mm
from config import *
from config import sx, sy
from colors import *
from calendar_engine import *
import themes
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'styles'))
from styles.manager import obter_estilo


def _est():
    return obter_estilo()


def desenhar_pagina_semanal(pdf, com_agendamentos=False):
    est = _est()

    est.pagina_semanal_titulo(pdf)

    dias = [
        ("SEG", CANDY_SEGUNDA), ("TER", CANDY_TERCA),
        ("QUA", CANDY_QUARTA), ("QUI", CANDY_QUINTA),
        ("SEX", CANDY_SEXTA), ("SAB", CANDY_SABADO),
        ("DOM", CANDY_DOMINGO)
    ]
    est.pagina_semanal_dias(pdf, dias)

    pw = LARGURA / mm
    ph = ALTURA / mm

    if com_agendamentos:
        est.pagina_semanal_prioridades(pdf, 8, ph - 85, 132, 25)
        est.caixa_agendamentos(pdf, 8, ph - 130, 132, 40)
        est.pagina_semanal_escrita(pdf, 8, 10, 132, ph - 144)
    else:
        est.pagina_semanal_prioridades(pdf, 8, ph - 85, 132, 30)
        est.pagina_semanal_escrita(pdf, 8, 10, 132, ph - 99)

    pdf.showPage()
