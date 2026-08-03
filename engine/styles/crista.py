import calendar
from datetime import date, timedelta
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'data'))
import config
from config import sx, sy
from colors import *
from .tema import Tema
from .estilo_base import EstiloBase
import localization
import themes

_FONT_B = "Helvetica-Bold"
_FONT = "Helvetica"
_FONT_O = "Helvetica-Oblique"

tema = Tema(
    nome="Crista",
    primaria="#FFFFFF",
    secundaria="#FDF8EE",
    destaque="#6B1E2A",
    texto="#4A3A33",
    texto_secundario="#8A7A6A",
    linhas="#E4D5B6",
    bordas="#C9A227",
    cabecalho="#6B1E2A",
    texto_cabecalho="#FFFFFF",
    prioridade="#6B1E2A",
    mini_borda="#E4D5B6",
    mini_texto="#4A3A33",
    mini_domingo="#C9A227",
    feriado="#C9A227",
    fonte_titulo="Helvetica-Bold",
    fonte_texto="Helvetica",
)

COR_BRANCO = HexColor("#FFFFFF")


def _para_hex(r, g, b):
    return "#%02X%02X%02X" % (max(0, min(255, int(round(r * 255)))),
                              max(0, min(255, int(round(g * 255)))),
                              max(0, min(255, int(round(b * 255)))))


def _escurecer(cor, fator):
    return HexColor(_para_hex(cor.red * (1 - fator),
                              cor.green * (1 - fator),
                              cor.blue * (1 - fator)))


def _clarear(cor, fator):
    return HexColor(_para_hex(cor.red + (1 - cor.red) * fator,
                              cor.green + (1 - cor.green) * fator,
                              cor.blue + (1 - cor.blue) * fator))


def atualizar_cores():
    """Deriva a paleta vinho/dourado da Agenda Crista a partir do tema ativo."""
    global COR_BORDO, COR_BORDO_CLARO, COR_GOLD, COR_GOLD_CLARO
    global COR_CREME, COR_LINHA, COR_LINHA_FORTE, COR_TEXTO_CABECALHO
    base = getattr(themes.tema_atual, 'importante', None)
    if base is None:
        base = getattr(themes.tema_atual, 'titulo', None)
    if base is None:
        base = HexColor("#EFA8BC")
    COR_BORDO = _escurecer(base, 0.60)
    COR_BORDO_CLARO = _escurecer(base, 0.32)
    COR_GOLD = _escurecer(base, 0.10)
    COR_GOLD_CLARO = _clarear(base, 0.70)
    COR_TEXTO_CABECALHO = _clarear(base, 0.55)
    COR_CREME = _clarear(base, 0.94)
    COR_LINHA = _clarear(base, 0.60)
    COR_LINHA_FORTE = _escurecer(base, 0.42)


atualizar_cores()


def _versiculo_do_dia(data):
    from versiculos import obter_versiculo
    return obter_versiculo(data.timetuple().tm_yday, localization.codigo_idioma())


class Crista(EstiloBase):
    nome = "Crista"

    # ------------------------------------------------------------ helpers
    def fundo_pagina(self, pdf):
        pdf.setFillColor(COR_CREME)
        pdf.rect(0, 0, config.LARGURA, config.ALTURA, fill=1, stroke=0)

    def _faixa_titulo(self, pdf, x, y, w, h, texto):
        """Faixa vinho com detalhe dourado para cabecalhos de pagina."""
        pdf.setFillColor(COR_BORDO)
        pdf.rect(sx(x * mm), sy(y * mm), sx(w * mm), sy(h * mm), fill=1, stroke=0)
        pdf.setFillColor(COR_GOLD)
        pdf.rect(sx(x * mm), sy((y + h - 1.5) * mm), sx(w * mm), sy(1.5 * mm), fill=1, stroke=0)
        pdf.setFillColor(COR_GOLD)
        pdf.rect(sx(x * mm), sy(y * mm), sx(2.2 * mm), sy(h * mm), fill=1, stroke=0)
        pdf.setFont(_FONT_B, 12)
        pdf.setFillColor(COR_BRANCO)
        pdf.drawCentredString(sx((x + w / 2) * mm), sy((y + h / 2 - 1.2) * mm), texto)

    def _cruz(self, pdf, x, y, size):
        """Cruz latina dourada (haste inferior mais longa, estilo igreja catolica)."""
        pdf.setStrokeColor(COR_GOLD)
        pdf.setLineWidth(0.7)
        pdf.line(sx(x * mm), sy(y * mm), sx(x * mm), sy((y + size) * mm))
        bar_y = y + size * 0.70
        half_w = size * 0.28
        pdf.line(sx((x - half_w) * mm), sy(bar_y * mm),
                 sx((x + half_w) * mm), sy(bar_y * mm))

    def _sino(self, pdf, x, y, size):
        """Sino de Belem: campainha dourada estilizada com alca, aba e badalo."""
        pdf.setStrokeColor(COR_GOLD)
        pdf.setLineWidth(0.5)
        top = y + size
        half = size * 0.42
        mouth = y + size * 0.35
        pdf.circle(sx(x * mm), sy((top - 0.5) * mm), 0.55 * mm, stroke=1, fill=0)
        pdf.line(sx((x - half) * mm), sy(mouth * mm), sx(x * mm), sy((top - 1.2) * mm))
        pdf.line(sx((x + half) * mm), sy(mouth * mm), sx(x * mm), sy((top - 1.2) * mm))
        pdf.line(sx((x - half - 0.7) * mm), sy(mouth * mm),
                 sx((x + half + 0.7) * mm), sy(mouth * mm))
        pdf.line(sx((x - half - 0.7) * mm), sy((mouth - 0.7) * mm),
                 sx((x + half + 0.7) * mm), sy((mouth - 0.7) * mm))
        pdf.setFillColor(COR_GOLD)
        pdf.circle(sx(x * mm), sy((mouth - 0.9) * mm), 0.4 * mm, stroke=0, fill=1)

    def _biblia(self, pdf, x, y, size):
        """Biblia aberta dourada: lombada central com paginas inclinadas."""
        pdf.setStrokeColor(COR_GOLD)
        pdf.setLineWidth(0.55)
        top = y + size
        half = size * 0.55
        pdf.line(sx(x * mm), sy((y + size * 0.10) * mm), sx(x * mm), sy(top * mm))
        pdf.line(sx(x * mm), sy(top * mm), sx((x - half) * mm), sy((y + size * 0.30) * mm))
        pdf.line(sx(x * mm), sy((y + size * 0.10) * mm), sx((x - half) * mm), sy((y + size * 0.18) * mm))
        pdf.line(sx((x - half) * mm), sy((y + size * 0.30) * mm),
                 sx((x - half) * mm), sy((y + size * 0.18) * mm))
        pdf.line(sx(x * mm), sy(top * mm), sx((x + half) * mm), sy((y + size * 0.30) * mm))
        pdf.line(sx(x * mm), sy((y + size * 0.10) * mm), sx((x + half) * mm), sy((y + size * 0.18) * mm))
        pdf.line(sx((x + half) * mm), sy((y + size * 0.30) * mm),
                 sx((x + half) * mm), sy((y + size * 0.18) * mm))

    def _canto(self, pdf, x, y, corner):
        pdf.setStrokeColor(COR_GOLD)
        pdf.setLineWidth(0.45)
        sz = 4
        if corner == "tl":
            pdf.line(sx(x * mm), sy(y * mm), sx((x + sz) * mm), sy(y * mm))
            pdf.line(sx(x * mm), sy(y * mm), sx(x * mm), sy((y - sz) * mm))
        elif corner == "tr":
            pdf.line(sx((x - sz) * mm), sy(y * mm), sx(x * mm), sy(y * mm))
            pdf.line(sx(x * mm), sy(y * mm), sx(x * mm), sy((y - sz) * mm))
        elif corner == "bl":
            pdf.line(sx(x * mm), sy(y * mm), sx((x + sz) * mm), sy(y * mm))
            pdf.line(sx(x * mm), sy(y * mm), sx(x * mm), sy((y + sz) * mm))
        elif corner == "br":
            pdf.line(sx((x - sz) * mm), sy(y * mm), sx(x * mm), sy(y * mm))
            pdf.line(sx(x * mm), sy(y * mm), sx(x * mm), sy((y + sz) * mm))

    def _borda_pagina(self, pdf):
        pw = config.LARGURA / mm
        ph = config.ALTURA / mm
        pdf.setStrokeColor(COR_GOLD)
        pdf.setLineWidth(0.6)
        pdf.rect(sx(5 * mm), sy(5 * mm), sx((pw - 10) * mm), sy((ph - 10) * mm), fill=0, stroke=1)
        pdf.setStrokeColor(COR_LINHA_FORTE)
        pdf.setLineWidth(0.35)
        pdf.rect(sx(7 * mm), sy(7 * mm), sx((pw - 14) * mm), sy((ph - 14) * mm), fill=0, stroke=1)
        self._canto(pdf, 5, ph - 5, "tl")
        self._canto(pdf, pw - 5, ph - 5, "tr")
        self._canto(pdf, 5, 5, "bl")
        self._canto(pdf, pw - 5, 5, "br")
        self._cruz(pdf, 12, ph - 12, 3)

    def _moldura_caixa(self, pdf, x, y, w, h, titulo):
        pdf.setFillColor(COR_CREME)
        pdf.setStrokeColor(COR_LINHA_FORTE)
        pdf.setLineWidth(0.4)
        pdf.rect(sx(x * mm), sy(y * mm), sx(w * mm), sy(h * mm), fill=1, stroke=1)
        pdf.setFillColor(COR_BORDO)
        pdf.rect(sx(x * mm), sy((y + h - 7) * mm), sx(w * mm), sy(7 * mm), fill=1, stroke=0)
        pdf.setFillColor(COR_GOLD)
        pdf.rect(sx(x * mm), sy((y + h - 7) * mm), sx(1.8 * mm), sy(7 * mm), fill=1, stroke=0)
        pdf.setFont(_FONT_B, 7)
        pdf.setFillColor(COR_BRANCO)
        pdf.drawString(sx((x + 4.5) * mm), sy((y + h - 5) * mm), titulo)

    def _linhas(self, pdf, x, y, w, h, intervalo=6, inicio=None):
        yy = y + h - 10 if inicio is None else inicio
        while yy >= y + 3:
            pdf.setStrokeColor(COR_LINHA)
            pdf.setLineWidth(0.2)
            pdf.line(sx((x + 3) * mm), sy(yy * mm), sx((x + w - 3) * mm), sy(yy * mm))
            yy -= intervalo

    def _quebrar(self, pdf, texto, fonte, tamanho, largura_mm):
        palavras = texto.split()
        linhas = []
        atual = ""
        for p in palavras:
            cand = (atual + " " + p).strip()
            if pdf.stringWidth(cand, fonte, tamanho) <= largura_mm * mm:
                atual = cand
            else:
                if atual:
                    linhas.append(atual)
                atual = p
        if atual:
            linhas.append(atual)
        return linhas

    # ------------------------------------------------------------ dados
    def pagina_dados_pessoais(self, pdf, campos):
        self.fundo_pagina(pdf)
        self._borda_pagina(pdf)
        pw = config.LARGURA / mm
        ph = config.ALTURA / mm
        self._faixa_titulo(pdf, 15, ph - 36, pw - 30, 17, localization.label("dados_pessoais"))
        pdf.setFont(_FONT, 7)
        pdf.setFillColor(COR_GOLD)
        pdf.drawCentredString(sx((pw / 2) * mm), sy((ph - 44) * mm),
                              localization.label("identificacao_profissional"))
        yy = ph - 54
        for campo in campos:
            pdf.setFont(_FONT_B, 8)
            pdf.setFillColor(COR_TEXTO_SEC if False else COR_BORDO)
            pdf.drawString(sx(20 * mm), sy(yy * mm), campo)
            pdf.setStrokeColor(COR_LINHA_FORTE)
            pdf.setLineWidth(0.3)
            pdf.line(sx(20 * mm), sy((yy - 2) * mm), sx((pw - 20) * mm), sy((yy - 2) * mm))
            pdf.setFillColor(COR_GOLD)
            pdf.rect(sx(20 * mm), sy((yy - 2) * mm), sx(1.5 * mm), sy(0.3 * mm), fill=1, stroke=0)
            yy -= 15
        pdf.showPage()

    # ------------------------------------------------------------ anual
    def pagina_calendario_anual(self, pdf, ano):
        self.fundo_pagina(pdf)
        self._borda_pagina(pdf)
        pw = config.LARGURA / mm
        ph = config.ALTURA / mm
        self._faixa_titulo(pdf, 8, ph - 16, pw - 16, 11,
                           localization.label("calendario_ano") % ano)

        margin_x = 9
        margin_top = ph - 21
        margin_bottom = 9
        cols = 4
        rows = 3
        gap_x = 4
        gap_y = 4
        cell_w = (pw - 2 * margin_x - (cols - 1) * gap_x) / cols
        cell_h = (margin_top - margin_bottom - (rows - 1) * gap_y) / rows

        dias_curto = localization._idioma_atual.get(
            'dias_semana_curto', ['S', 'T', 'Q', 'Q', 'S', 'S', 'D'])
        meses = localization._idioma_atual.get(
            'meses', {1: 'Janeiro', 2: 'Fevereiro', 3: 'Marco', 4: 'Abril',
                      5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto',
                      9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'})

        for mes in range(1, 13):
            idx = mes - 1
            col = idx % cols
            row = idx // cols
            cx = margin_x + col * (cell_w + gap_x)
            cy = margin_top - row * (cell_h + gap_y) - cell_h

            pdf.setFillColor(COR_BRANCO)
            pdf.setStrokeColor(COR_LINHA_FORTE)
            pdf.setLineWidth(0.35)
            pdf.rect(sx(cx * mm), sy(cy * mm), sx(cell_w * mm), sy(cell_h * mm), fill=1, stroke=1)

            pdf.setFillColor(COR_BORDO)
            pdf.rect(sx(cx * mm), sy((cy + cell_h - 6.5) * mm), sx(cell_w * mm), sy(6.5 * mm), fill=1, stroke=0)
            pdf.setFillColor(COR_GOLD)
            pdf.rect(sx(cx * mm), sy((cy + cell_h - 6.5) * mm), sx(1.2 * mm), sy(6.5 * mm), fill=1, stroke=0)
            pdf.setFont(_FONT_B, 6)
            pdf.setFillColor(COR_BRANCO)
            pdf.drawCentredString(sx((cx + cell_w / 2) * mm), sy((cy + cell_h - 5) * mm), meses[mes].upper())

            day_label_y = cy + cell_h - 11
            day_w = cell_w / 7
            pdf.setFont(_FONT_B, 4.5)
            pdf.setFillColor(COR_BORDO)
            for d in range(7):
                dx = cx + d * day_w + day_w / 2
                pdf.drawCentredString(sx(dx * mm), sy(day_label_y * mm), dias_curto[d])

            cal = calendar.monthcalendar(ano, mes)
            start_y = day_label_y - 4
            row_h = (start_y - cy - 1.5) / max(len(cal), 1)
            for wi, week in enumerate(cal):
                for di, day in enumerate(week):
                    if day != 0:
                        dx = cx + di * day_w + day_w / 2
                        dy = start_y - wi * row_h
                        if di == 6:
                            pdf.setFillColor(COR_GOLD)
                        else:
                            pdf.setFillColor(COR_BORDO_CLARO)
                        pdf.setFont(_FONT, 4.5)
                        pdf.drawCentredString(sx(dx * mm), sy((dy - 5) * mm), str(day))

        pdf.showPage()

    # ------------------------------------------------------------ planejamento
    def planejamento(self, pdf, caixas):
        self.fundo_pagina(pdf)
        self._borda_pagina(pdf)
        pw = config.LARGURA / mm
        ph = config.ALTURA / mm
        self._faixa_titulo(pdf, 8, ph - 16, pw - 16, 11, localization.label("planejamento"))
        for titulo, y, alt in caixas:
            self._moldura_caixa(pdf, 15, y, 118, alt, titulo.upper())
            self._linhas(pdf, 15, y, 118, alt, intervalo=4)
        pdf.showPage()

    # ------------------------------------------------------------ diario
    def pagina_diaria(self, pdf, data, com_agendamentos=False):
        self.fundo_pagina(pdf)
        self._borda_pagina(pdf)
        pw = config.LARGURA / mm
        ph = config.ALTURA / mm

        # cabecalho
        pdf.setFillColor(COR_BORDO)
        pdf.rect(sx(8 * mm), sy((ph - 24) * mm), sx((pw - 16) * mm), sy(16 * mm), fill=1, stroke=0)
        pdf.setFillColor(COR_GOLD)
        pdf.rect(sx(8 * mm), sy((ph - 24) * mm), sx(2.2 * mm), sy(16 * mm), fill=1, stroke=0)
        pdf.setFont(_FONT_B, 28)
        pdf.setFillColor(COR_BRANCO)
        pdf.drawString(sx(15 * mm), sy((ph - 19) * mm), data.strftime("%d"))
        pdf.setFont(_FONT_B, 10)
        pdf.setFillColor(COR_GOLD_CLARO)
        pdf.drawString(sx(32 * mm), sy((ph - 16) * mm), localization.nome_dia(data).upper())
        pdf.setFont(_FONT, 7)
        pdf.setFillColor(COR_TEXTO_CABECALHO)
        pdf.drawString(sx(32 * mm), sy((ph - 21.5) * mm), data.strftime("%d/%m/%Y"))
        pdf.setFont(_FONT, 6.5)
        pdf.setFillColor(COR_TEXTO_CABECALHO)
        pdf.drawRightString(sx((pw - 12) * mm), sy((ph - 15) * mm),
                            localization.nome_mes(data.month).upper() + " " + str(data.year))
        self._cruz(pdf, pw - 13, ph - 10, 4)

        # versiculo do dia
        versiculo = _versiculo_do_dia(data)
        pdf.setFillColor(COR_CREME)
        pdf.setStrokeColor(COR_GOLD)
        pdf.setLineWidth(0.5)
        pdf.rect(sx(8 * mm), sy((ph - 41) * mm), sx((pw - 16) * mm), sy(14 * mm), fill=1, stroke=1)
        biblia_size = 4.5
        biblia_y = ph - 34 - biblia_size / 2
        self._biblia(pdf, 14, biblia_y, biblia_size)
        self._biblia(pdf, pw - 14, biblia_y, biblia_size)
        pdf.setFont(_FONT_O, 7.5)
        pdf.setFillColor(COR_BORDO)
        linhas = self._quebrar(pdf, versiculo["texto"], _FONT_O, 7.5, pw - 30)[:2]
        n = len(linhas)
        base_y = ph - 39 + (3 if n == 1 else 4)
        for i, linha in enumerate(linhas):
            pdf.drawCentredString(sx((pw / 2) * mm), sy((base_y - i * 3.6) * mm), linha)
        pdf.setFont(_FONT_B, 6)
        pdf.setFillColor(COR_GOLD)
        pdf.drawCentredString(sx((pw / 2) * mm), sy((ph - 43) * mm), versiculo["referencia"])

        if com_agendamentos:
            self._moldura_caixa(pdf, 8, ph - 46, pw - 16, 11,
                                localization.label("compromissos_horarios"))
            sched_y = ph - 128
            sched_h = ph - 46 - 8 - sched_y
            pdf.setStrokeColor(COR_LINHA)
            pdf.setLineWidth(0.2)
            n_slots = 11
            slot_h = sched_h / n_slots
            for i in range(n_slots):
                hora = 8 + i
                slot_y = ph - 46 - 8 - i * slot_h
                pdf.setFont(_FONT_B, 5.5)
                pdf.setFillColor(COR_BORDO)
                pdf.drawString(sx(11 * mm), sy((slot_y - 1.5) * mm), "%02d:00" % hora)
                pdf.setStrokeColor(COR_LINHA)
                pdf.setLineWidth(0.2)
                pdf.line(sx(24 * mm), sy((slot_y - 2) * mm), sx((pw - 12) * mm), sy((slot_y - 2) * mm))
            self._moldura_caixa(pdf, 8, 14, pw - 16, 28, localization.label("anotacoes_dia"))
            self._linhas(pdf, 8, 14, pw - 16, 28, intervalo=5)
        else:
            self._moldura_caixa(pdf, 8, ph - 46, pw - 16, 12, localization.label("prioridades"))
            self._linhas(pdf, 8, ph - 46, pw - 16, 12, intervalo=4)
            self._moldura_caixa(pdf, 8, 14, pw - 16, ph - 60, localization.label("anotacoes_dia"))
            self._linhas(pdf, 8, 14, pw - 16, ph - 60, intervalo=6)

        # rodape
        pdf.setFont(_FONT_B, 5.5)
        pdf.setFillColor(COR_GOLD)
        pdf.drawCentredString(sx((pw / 2 - 4) * mm), sy(9 * mm), versiculo["referencia"])
        self._cruz(pdf, pw / 2 - 4, 12, 3.5)
        self._sino(pdf, pw / 2 + 13, 14, 4.5)

        pdf.showPage()

    # ------------------------------------------------------------ 2dpp
    def _metade_2dpp(self, pdf, data, base_y, alt, espelhar=False, com_agendamentos=False):
        pw = config.LARGURA / mm
        top_pad = alt * 0.02
        bottom_pad = alt * 0.03
        header_h = alt * 0.13
        verse_h = alt * 0.12
        prior_h = alt * 0.12
        gap = alt * 0.015

        header_y = base_y + alt - top_pad - header_h
        verse_y = header_y - gap - verse_h
        prior_y = verse_y - gap - prior_h
        notes_y = base_y + bottom_pad
        notes_h = prior_y - gap - notes_y

        pdf.setFillColor(COR_BORDO)
        pdf.rect(sx(8 * mm), sy(header_y * mm), sx((pw - 16) * mm), sy(header_h * mm), fill=1, stroke=0)
        pdf.setFillColor(COR_GOLD)
        if espelhar:
            pdf.rect(sx((pw - 10.2) * mm), sy(header_y * mm), sx(2.2 * mm), sy(header_h * mm), fill=1, stroke=0)
            pdf.setFont(_FONT_B, 20)
            pdf.setFillColor(COR_BRANCO)
            pdf.drawRightString(sx((pw - 12) * mm), sy((header_y + header_h * 0.45) * mm), data.strftime("%d"))
            pdf.setFont(_FONT_B, 8)
            pdf.setFillColor(COR_GOLD_CLARO)
            pdf.drawString(sx(14 * mm), sy((header_y + header_h * 0.62) * mm), localization.nome_dia(data).upper())
            pdf.setFont(_FONT, 6)
            pdf.setFillColor(COR_TEXTO_CABECALHO)
            pdf.drawString(sx(14 * mm), sy((header_y + header_h * 0.22) * mm), data.strftime("%d/%m/%Y"))
            pdf.setFont(_FONT_B, 5.5)
            pdf.setFillColor(COR_TEXTO_CABECALHO)
            pdf.drawString(sx(14 * mm), sy((header_y + header_h * 0.45) * mm),
                            localization.nome_mes(data.month).upper() + " " + str(data.year))
            self._cruz(pdf, pw - 15, header_y + header_h * 0.5, 2.5)
        else:
            pdf.rect(sx(8 * mm), sy(header_y * mm), sx(2.2 * mm), sy(header_h * mm), fill=1, stroke=0)
            pdf.setFont(_FONT_B, 20)
            pdf.setFillColor(COR_BRANCO)
            pdf.drawString(sx(15 * mm), sy((header_y + header_h * 0.45) * mm), data.strftime("%d"))
            pdf.setFont(_FONT_B, 8)
            pdf.setFillColor(COR_GOLD_CLARO)
            pdf.drawRightString(sx((pw - 12) * mm), sy((header_y + header_h * 0.62) * mm),
                                 localization.nome_dia(data).upper())
            pdf.setFont(_FONT, 6)
            pdf.setFillColor(COR_TEXTO_CABECALHO)
            pdf.drawRightString(sx((pw - 12) * mm), sy((header_y + header_h * 0.22) * mm), data.strftime("%d/%m/%Y"))
            pdf.setFont(_FONT_B, 5.5)
            pdf.setFillColor(COR_TEXTO_CABECALHO)
            pdf.drawRightString(sx((pw - 12) * mm), sy((header_y + header_h * 0.45) * mm),
                                localization.nome_mes(data.month).upper() + " " + str(data.year))
            self._cruz(pdf, 14, header_y + header_h * 0.5, 2.5)

        versiculo = _versiculo_do_dia(data)
        pdf.setFillColor(COR_CREME)
        pdf.setStrokeColor(COR_GOLD)
        pdf.setLineWidth(0.4)
        pdf.rect(sx(8 * mm), sy(verse_y * mm), sx((pw - 16) * mm), sy(verse_h * mm), fill=1, stroke=1)
        biblia_size = 4.5
        self._biblia(pdf, 14, verse_y + (verse_h - biblia_size) / 2, biblia_size)
        self._biblia(pdf, pw - 14, verse_y + (verse_h - biblia_size) / 2, biblia_size)
        pdf.setFont(_FONT_O, 6.5)
        pdf.setFillColor(COR_BORDO)
        linhas = self._quebrar(pdf, versiculo["texto"], _FONT_O, 6.5, pw - 28)[:2]
        n = len(linhas)
        base_txt = verse_y + verse_h * 0.58
        for i, linha in enumerate(linhas):
            pdf.drawCentredString(sx((pw / 2) * mm), sy((base_txt - i * 3.2) * mm), linha)
        pdf.setFont(_FONT_B, 5.5)
        pdf.setFillColor(COR_GOLD)
        pdf.drawCentredString(sx((pw / 2) * mm), sy((verse_y + verse_h * 0.12) * mm), versiculo["referencia"])

        self._moldura_caixa(pdf, 8, prior_y, pw - 16, prior_h, localization.label("prioridades"))
        self._linhas(pdf, 8, prior_y, pw - 16, prior_h, intervalo=4)

        if com_agendamentos:
            sched_w = (pw - 16) * 0.36
            sched_x = 8 + (pw - 16) - sched_w
            notes_w = (pw - 16) - sched_w - 3
            self._moldura_caixa(pdf, sched_x, notes_y, sched_w, notes_h, localization.label("agendamentos"))
            n_slots = 11
            slot_h = (notes_h - 9) / n_slots
            for i in range(n_slots):
                hora = 8 + i
                slot_y = notes_y + notes_h - 9 - i * slot_h
                pdf.setFont(_FONT_B, 4.5)
                pdf.setFillColor(COR_BORDO)
                pdf.drawString(sx((sched_x + 2) * mm), sy((slot_y - 1.5) * mm), "%02d:00" % hora)
                pdf.setStrokeColor(COR_LINHA)
                pdf.setLineWidth(0.2)
                pdf.line(sx((sched_x + sched_w * 0.4) * mm), sy((slot_y - 2) * mm),
                         sx((sched_x + sched_w - 2) * mm), sy((slot_y - 2) * mm))
            self._moldura_caixa(pdf, 8, notes_y, notes_w, notes_h, localization.label("anotacoes_dia"))
            self._linhas(pdf, 8, notes_y, notes_w, notes_h, intervalo=4.5)
        else:
            self._moldura_caixa(pdf, 8, notes_y, pw - 16, notes_h, localization.label("anotacoes_dia"))
            self._linhas(pdf, 8, notes_y, pw - 16, notes_h, intervalo=4.5)

    def pagina_diaria_2dias(self, pdf, data1, data2, com_agendamentos=False):
        self.fundo_pagina(pdf)
        self._borda_pagina(pdf)
        pw = config.LARGURA / mm
        ph = config.ALTURA / mm
        alt = ph / 2
        self._metade_2dpp(pdf, data1, alt, alt, espelhar=False, com_agendamentos=com_agendamentos)
        if data2 is not None:
            self._metade_2dpp(pdf, data2, 0, alt, espelhar=True, com_agendamentos=com_agendamentos)
        pdf.setStrokeColor(COR_GOLD)
        pdf.setLineWidth(0.4)
        pdf.line(sx(8 * mm), sy(alt * mm), sx((pw - 8) * mm), sy(alt * mm))
        pdf.showPage()


estilo = Crista()
