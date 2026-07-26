from colors import *

class AgendaTheme:
    nome = "Padrao"
    fundo = BRANCO
    texto = PRETO
    texto_secundario = CINZA
    texto_cabecalho = BRANCO
    linha = LINHA
    linhas = linha
    bordas = linha
    titulo = ROSA
    cabecalho = titulo
    tarefas = VERDE
    primaria = tarefas
    importante = ROSA
    prioridade = importante
    gratidao = AZUL
    secundaria = gratidao
    calendario = LILAS
    destaque = ROSA_ESCURO
    mini_borda = linha
    mini_texto = texto
    mini_domingo = VERMELHO
    feriado = VERMELHO

class FloralTheme(AgendaTheme):
    nome = "Floral"
    titulo = HexColor("#F7CAD0")
    tarefas = HexColor("#CDEAC0")
    importante = HexColor("#FFD6E0")
    gratidao = HexColor("#DDEEFF")

class KawaiiTheme(AgendaTheme):
    nome = "Kawaii"
    titulo = HexColor("#FFD1DC")
    tarefas = HexColor("#B5EAD7")
    importante = HexColor("#FFDAC1")
    gratidao = HexColor("#C7CEEA")

class MinimalTheme(AgendaTheme):
    nome = "Minimal"
    titulo = HexColor("#ECECEC")
    tarefas = HexColor("#FFFFFF")
    importante = HexColor("#F5F5F5")
    gratidao = HexColor("#F8F8F8")

class RosaTheme(AgendaTheme):
    nome = "Rosa"
    titulo = ROSA
    tarefas = ROSA
    importante = ROSA_ESCURO
    gratidao = ROSA
    calendario = ROSA
    destaque = ROSA_ESCURO

class AzulTheme(AgendaTheme):
    nome = "Azul"
    titulo = AZUL
    tarefas = AZUL
    importante = AZUL_ESCURO
    gratidao = AZUL
    calendario = AZUL
    destaque = AZUL_ESCURO

class VerdeTheme(AgendaTheme):
    nome = "Verde"
    titulo = VERDE
    tarefas = VERDE
    importante = VERDE_ESCURO
    gratidao = VERDE
    calendario = VERDE
    destaque = VERDE_ESCURO

class AmareloTheme(AgendaTheme):
    nome = "Amarelo"
    titulo = AMARELO
    tarefas = AMARELO
    importante = HexColor("#E5B94B")
    gratidao = AMARELO
    calendario = AMARELO
    destaque = HexColor("#E5B94B")

class LaranjaTheme(AgendaTheme):
    nome = "Laranja"
    titulo = LARANJA
    tarefas = LARANJA
    importante = HexColor("#F39C4A")
    gratidao = LARANJA
    calendario = LARANJA
    destaque = HexColor("#F39C4A")

class VermelhoTheme(AgendaTheme):
    nome = "Vermelho"
    titulo = VERMELHO
    tarefas = VERMELHO
    importante = HexColor("#D94B4B")
    gratidao = VERMELHO
    calendario = VERMELHO
    destaque = HexColor("#D94B4B")

class LilasTheme(AgendaTheme):
    nome = "Lilas"
    titulo = LILAS
    tarefas = LILAS
    importante = HexColor("#B48DD8")
    gratidao = LILAS
    calendario = LILAS
    destaque = HexColor("#B48DD8")

class PretoTheme(AgendaTheme):
    nome = "Preto"
    titulo = CINZA
    tarefas = CINZA
    importante = PRETO
    gratidao = CINZA
    calendario = CINZA
    destaque = PRETO
    texto = BRANCO

tema_atual = RosaTheme()

def definir(tema):
    global tema_atual
    tema_atual = tema


def criar_tema_da_ia(colors_list):
    """Create a dynamic theme from AI-detected colors."""
    class DynamicTheme(AgendaTheme):
        nome = "IA Custom"
        pass

    t = DynamicTheme()

    for c in colors_list:
        role = c.get("role", "")
        hex_val = c.get("hex", "")
        if not hex_val:
            continue
        try:
            color = HexColor(hex_val)
        except Exception:
            continue

        if role == "accent":
            t.titulo = color
            t.cabecalho = color
            t.calendario = color
            t.destaque = color
        elif role == "primary":
            t.titulo = color
            t.cabecalho = color
        elif role == "background":
            t.fundo = color
        elif role == "text":
            t.texto = color
            t.texto_secundario = color
        elif role == "highlight":
            t.importante = color
            t.prioridade = color
        elif role == "border":
            t.linha = color
            t.linhas = color
            t.bordas = color

    accent = t.titulo
    t.tarefas = accent
    t.primaria = accent
    t.gratidao = accent
    t.secundaria = accent

    return t
