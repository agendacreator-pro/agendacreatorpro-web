from .minimalista import estilo as estilo_minimalista, tema as tema_minimalista
from .executivo import estilo as estilo_executivo, tema as tema_executivo
from .floral import estilo as estilo_floral, tema as tema_floral
from .kawaii import estilo as estilo_kawaii, tema as tema_kawaii
from .juridico import estilo as estilo_juridico, tema as tema_juridico

ESTILOS = {
    "minimalista": (estilo_minimalista, tema_minimalista),
    "executivo": (estilo_executivo, tema_executivo),
    "floral": (estilo_floral, tema_floral),
    "kawaii": (estilo_kawaii, tema_kawaii),
    "juridico": (estilo_juridico, tema_juridico),
}

estilo_atual = estilo_minimalista
tema_atual = tema_minimalista

def definir(nome):
    global estilo_atual, tema_atual
    estilo_atual, tema_atual = ESTILOS.get(
        str(nome).lower(),
        (estilo_minimalista, tema_minimalista)
    )

def obter_estilo():
    return estilo_atual

def obter_tema():
    return tema_atual
