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


def desenhar_pagina_semanal(pdf):
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

    est.pagina_semanal_prioridades(pdf, 8, ph - 102, 132, 36)
    est.pagina_semanal_escrita(pdf, 8, 12, 132, ph - 118)

    pdf.showPage()
