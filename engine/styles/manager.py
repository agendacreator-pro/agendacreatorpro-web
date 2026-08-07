from .minimalista import estilo as estilo_minimalista, tema as tema_minimalista
from .executivo import estilo as estilo_executivo, tema as tema_executivo
from .floral import estilo as estilo_floral, tema as tema_floral
from .kawaii import estilo as estilo_kawaii, tema as tema_kawaii
from .juridico import estilo as estilo_juridico, tema as tema_juridico
from .crista import estilo as estilo_crista, tema as tema_crista
from . import minimalista, executivo, floral, kawaii, juridico, crista, estilo_base

ESTILOS = {
    "minimalista": (estilo_minimalista, tema_minimalista),
    "executivo": (estilo_executivo, tema_executivo),
    "floral": (estilo_floral, tema_floral),
    "kawaii": (estilo_kawaii, tema_kawaii),
    "juridico": (estilo_juridico, tema_juridico),
    "crista": (estilo_crista, tema_crista),
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

_FONTES_PADRAO = {
    "_FONT": "Helvetica",
    "_FONT_B": "Helvetica-Bold",
    "_FONT_O": "Helvetica-Oblique",
}

def _modulos_fonte():
    mods = [minimalista, executivo, floral, kawaii, juridico, crista, estilo_base]
    try:
        import layouts_base
        import layouts_a5
        mods += [layouts_base, layouts_a5]
    except Exception:
        pass
    return mods

def definir_fonte(familia):
    """Aplica uma fonte registrada (engine/fonts.py) a todos os desenhos de texto.

    familia=None restaura Helvetica. Troca os globais _FONT/_FONT_B/_FONT_O de
    todos os modulos de estilo e layouts que os usam em setFont(), alem de
    atualizar config.FONTE / config.FONTE_NEGRITO.
    """
    import config
    from fonts import resolve_font

    if familia:
        fontes = {
            "_FONT": resolve_font(familia, False, False),
            "_FONT_B": resolve_font(familia, True, False),
            "_FONT_O": resolve_font(familia, False, True),
        }
    else:
        fontes = {}

    for mod in _modulos_fonte():
        for attr, valor in fontes.items():
            if hasattr(mod, attr):
                setattr(mod, attr, valor or _FONTES_PADRAO.get(attr))
        if not fontes:
            for attr, valor in _FONTES_PADRAO.items():
                if hasattr(mod, attr):
                    setattr(mod, attr, valor)

    config.FONTE = fontes.get("_FONT") or "Helvetica"
    config.FONTE_NEGRITO = fontes.get("_FONT_B") or "Helvetica-Bold"
