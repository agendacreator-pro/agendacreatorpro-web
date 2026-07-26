from reportlab.lib.units import mm

FORMATO = "A5"

LARGURA = 148 * mm
ALTURA = 210 * mm

def obter_tamanho_pagina(formato="A5"):
    formato = formato.upper()
    if formato == "A4":
        return 210 * mm, 297 * mm
    elif formato == "QUADRADO":
        return 150 * mm, 150 * mm
    return 148 * mm, 210 * mm

LARGURA_BASE = 148 * mm
ALTURA_BASE = 210 * mm

ESCALA_X = 1.0
ESCALA_Y = 1.0

def atualizar_escala():
    global ESCALA_X, ESCALA_Y
    ESCALA_X = LARGURA / LARGURA_BASE
    ESCALA_Y = ALTURA / ALTURA_BASE

def sx(x_mm):
    return x_mm * ESCALA_X

def sy(y_mm):
    return y_mm * ESCALA_Y

MARGEM_ESQ = 15 * mm
MARGEM_DIR = 15 * mm

AREA_UTIL = LARGURA - MARGEM_ESQ - MARGEM_DIR

FONTE = "Helvetica"
FONTE_NEGRITO = "Helvetica-Bold"

TITULO = 18
SUBTITULO = 12
NORMAL = 10
PEQUENO = 8
MINI = 6
