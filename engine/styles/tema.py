from dataclasses import dataclass

@dataclass
class Tema:
    nome: str
    primaria: str
    secundaria: str
    destaque: str
    texto: str
    texto_secundario: str
    linhas: str
    bordas: str = "#BFBFBF"
    cabecalho: str = "#000000"
    texto_cabecalho: str = "#FFFFFF"
    prioridade: str = "#000000"
    mini_borda: str = "#BFBFBF"
    mini_texto: str = "#000000"
    mini_domingo: str = "#D62828"
    feriado: str = "#D62828"
    fonte_titulo: str = "Helvetica-Bold"
    fonte_texto: str = "Helvetica"
