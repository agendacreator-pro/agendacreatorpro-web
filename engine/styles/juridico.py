import math
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
from frases_prosperidade import obter_frase

_FONT_B = "Helvetica-Bold"
_FONT = "Helvetica"
_FONT_O = "Helvetica-Oblique"

tema = Tema(
    nome="Juridico",
    primaria="#FFFFFF",
    secundaria="#F4F1EB",
    destaque="#1B2A4A",
    texto="#1B2A4A",
    texto_secundario="#6B7280",
    linhas="#C9CFDA",
    bordas="#94A3B8",
    cabecalho="#1B2A4A",
    texto_cabecalho="#FFFFFF",
    prioridade="#1B2A4A",
    mini_borda="#C9CFDA",
    mini_texto="#1B2A4A",
    mini_domingo="#B91C1C",
    feriado="#B91C1C",
    fonte_titulo="Helvetica-Bold",
    fonte_texto="Helvetica",
)

COR_BRANCO = HexColor("#FFFFFF")
COR_TEXTO_SEC = HexColor("#5F6B7A")


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
    """Deriva a paleta navy/dourado da Agenda Juridica a partir do tema ativo."""
    global COR_NAVY, COR_NAVY_CLARO, COR_GOLD, COR_GOLD_CLARO
    global COR_CREME, COR_LINHA, COR_LINHA_FORTE, COR_TEXTO_CABECALHO
    base = getattr(themes.tema_atual, 'importante', None)
    if base is None:
        base = getattr(themes.tema_atual, 'titulo', None)
    if base is None:
        base = HexColor("#EFA8BC")
    COR_NAVY = _escurecer(base, 0.55)
    COR_NAVY_CLARO = _escurecer(base, 0.30)
    COR_GOLD = _escurecer(base, 0.08)
    COR_GOLD_CLARO = _clarear(base, 0.72)
    COR_TEXTO_CABECALHO = _clarear(base, 0.55)
    COR_CREME = _clarear(base, 0.93)
    COR_LINHA = _clarear(base, 0.82)
    COR_LINHA_FORTE = _escurecer(base, 0.42)


atualizar_cores()


def _traducao_maxima(maxima):
    cod = localization.codigo_idioma()
    if cod == 'en':
        return maxima.get('traducao_en') or maxima['traducao']
    if cod == 'es':
        return maxima.get('traducao_es') or maxima['traducao']
    return maxima['traducao']


def _frase_do_dia(data):
    return obter_frase(data.timetuple().tm_yday, localization.codigo_idioma())


class Juridico(EstiloBase):
    nome = "Juridico"

    # ------------------------------------------------------------ helpers
    def fundo_pagina(self, pdf):
        pdf.setFillColor(BRANCO)
        pdf.rect(0, 0, config.LARGURA, config.ALTURA, fill=1, stroke=0)

    def _faixa_titulo(self, pdf, x, y, w, h, texto):
        """Faixa azul-marinho com detalhe dourado no topo da pagina."""
        pdf.setFillColor(COR_NAVY)
        pdf.rect(sx(x * mm), sy(y * mm), sx(w * mm), sy(h * mm), fill=1, stroke=0)
        pdf.setFillColor(COR_GOLD)
        pdf.rect(sx(x * mm), sy((y + h - 1.6) * mm), sx(w * mm), sy(1.6 * mm), fill=1, stroke=0)
        pdf.setFillColor(COR_GOLD)
        pdf.rect(sx(x * mm), sy(y * mm), sx(2.2 * mm), sy(h * mm), fill=1, stroke=0)
        pdf.setFont(_FONT_B, 12)
        pdf.setFillColor(COR_BRANCO)
        pdf.drawCentredString(sx((x + w / 2) * mm), sy((y + h / 2 - 1.2) * mm), texto)

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
        pdf.setStrokeColor(COR_LINHA_FORTE)
        pdf.setLineWidth(0.4)
        pdf.rect(sx(5 * mm), sy(5 * mm), sx((pw - 10) * mm), sy((ph - 10) * mm), fill=0, stroke=1)
        self._canto(pdf, 5, ph - 5, "tl")
        self._canto(pdf, pw - 5, ph - 5, "tr")
        self._canto(pdf, 5, 5, "bl")
        self._canto(pdf, pw - 5, 5, "br")

    def _moldura_caixa(self, pdf, x, y, w, h, titulo, cor_fundo=COR_CREME):
        pdf.setFillColor(cor_fundo)
        pdf.setStrokeColor(COR_LINHA_FORTE)
        pdf.setLineWidth(0.45)
        pdf.rect(sx(x * mm), sy(y * mm), sx(w * mm), sy(h * mm), fill=1, stroke=1)
        pdf.setFillColor(COR_NAVY)
        pdf.rect(sx(x * mm), sy((y + h - 7) * mm), sx(w * mm), sy(7 * mm), fill=1, stroke=0)
        pdf.setFillColor(COR_GOLD)
        pdf.rect(sx(x * mm), sy((y + h - 7) * mm), sx(1.8 * mm), sy(7 * mm), fill=1, stroke=0)
        pdf.setFont(_FONT_B, 7)
        pdf.setFillColor(COR_BRANCO)
        pdf.drawString(sx((x + 4.5) * mm), sy((y + h - 5) * mm), titulo)

    def _linhas(self, pdf, x, y, w, h, intervalo=6, inicio=None):
        yy = y + h - 9 if inicio is None else inicio
        while yy >= y + 3:
            pdf.setStrokeColor(COR_LINHA)
            pdf.setLineWidth(0.2)
            pdf.line(sx((x + 3) * mm), sy(yy * mm), sx((x + w - 3) * mm), sy(yy * mm))
            yy -= intervalo

    # ------------------------------------------------------------ dados
    def pagina_dados(self, pdf):
        self.fundo_pagina(pdf)
        self._borda_pagina(pdf)
        pw = config.LARGURA / mm
        ph = config.ALTURA / mm
        self._faixa_titulo(pdf, 15, ph - 36, pw - 30, 17, localization.label("dados_pessoais"))
        pdf.setFont(_FONT, 7)
        pdf.setFillColor(COR_TEXTO_SEC)
        pdf.drawCentredString(sx((pw / 2) * mm), sy((ph - 44) * mm),
                              localization.label("identificacao_profissional"))

        campos_advogado = [
            localization.label("nome_completo"),
            localization.label("oab_uf"),
            localization.label("telefone_celular"),
            localization.label("email"),
            localization.label("endereco_escritorio"),
            localization.label("cidade_uf"),
            localization.label("especialidades"),
        ]
        yy = ph - 54
        for campo in campos_advogado:
            pdf.setFont(_FONT_B, 8)
            pdf.setFillColor(COR_TEXTO_SEC)
            pdf.drawString(sx(20 * mm), sy(yy * mm), campo)
            pdf.setStrokeColor(COR_LINHA_FORTE)
            pdf.setLineWidth(0.3)
            pdf.line(sx(20 * mm), sy((yy - 2) * mm), sx((pw - 20) * mm), sy((yy - 2) * mm))
            pdf.setFillColor(COR_GOLD)
            pdf.rect(sx(20 * mm), sy((yy - 2) * mm), sx(1.5 * mm), sy(0.3 * mm), fill=1, stroke=0)
            yy -= 15

        self._moldura_caixa(pdf, 15, 44, pw - 30, 44, localization.label("dados_escritorio"))
        campos_escritorio = [
            (localization.label("razao_social"), localization.label("cnpj")),
            (localization.label("nome_fantasia"), localization.label("registro_oab")),
            (localization.label("endereco"), localization.label("telefone")),
        ]
        fx = 19
        for rotulo, rotulo2 in campos_escritorio:
            pdf.setFont(_FONT_B, 6.5)
            pdf.setFillColor(COR_TEXTO_SEC)
            pdf.drawString(sx(fx * mm), sy((74 - (campos_escritorio.index((rotulo, rotulo2)) * 12)) * mm), rotulo)
            pdf.drawString(sx((fx + 62) * mm), sy((74 - (campos_escritorio.index((rotulo, rotulo2)) * 12)) * mm), rotulo2)
            pdf.setStrokeColor(COR_LINHA)
            pdf.setLineWidth(0.2)
            pdf.line(sx(fx * mm), sy((72 - (campos_escritorio.index((rotulo, rotulo2)) * 12)) * mm),
                     sx((fx + 58) * mm), sy((72 - (campos_escritorio.index((rotulo, rotulo2)) * 12)) * mm))
            pdf.line(sx((fx + 62) * mm), sy((72 - (campos_escritorio.index((rotulo, rotulo2)) * 12)) * mm),
                     sx((pw - 20) * mm), sy((72 - (campos_escritorio.index((rotulo, rotulo2)) * 12)) * mm))

        pdf.setFont(_FONT, 6)
        pdf.setFillColor(COR_TEXTO_SEC)
        pdf.drawCentredString(sx((pw / 2) * mm), sy(18 * mm),
                              localization.label("agenda_juridica_ano") % date.today().year)
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

            pdf.setFillColor(COR_NAVY)
            pdf.rect(sx(cx * mm), sy((cy + cell_h - 6.5) * mm), sx(cell_w * mm), sy(6.5 * mm), fill=1, stroke=0)
            pdf.setFillColor(COR_GOLD)
            pdf.rect(sx(cx * mm), sy((cy + cell_h - 6.5) * mm), sx(1.2 * mm), sy(6.5 * mm), fill=1, stroke=0)
            pdf.setFont(_FONT_B, 6)
            pdf.setFillColor(COR_BRANCO)
            pdf.drawCentredString(sx((cx + cell_w / 2) * mm), sy((cy + cell_h - 5) * mm), meses[mes].upper())

            day_label_y = cy + cell_h - 11
            day_w = cell_w / 7
            pdf.setFont(_FONT_B, 4.5)
            pdf.setFillColor(COR_NAVY)
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
                            pdf.setFillColor(COR_NAVY_CLARO)
                        pdf.setFont(_FONT, 4.5)
                        pdf.drawCentredString(sx(dx * mm), sy((dy - 5) * mm), str(day))

        pdf.showPage()

    # ------------------------------------------------------------ mensal
    def pagina_mensal(self, pdf, data):
        self.fundo_pagina(pdf)
        self._borda_pagina(pdf)
        pw = config.LARGURA / mm
        ph = config.ALTURA / mm

        titulo = localization.nome_mes(data.month).upper() + " " + str(data.year)
        self._faixa_titulo(pdf, 8, ph - 16, pw - 16, 11, titulo)

        dias_curto = localization._idioma_atual.get(
            'dias_semana_curto', ['S', 'T', 'Q', 'Q', 'S', 'S', 'D'])
        cal = calendar.monthcalendar(data.year, data.month)

        gx = 12
        gw = pw - 24

        self._moldura_caixa(pdf, 12, ph - 44, gw, 22, localization.label("prazos_mes"))
        self._linhas(pdf, 12, ph - 44, gw, 22, intervalo=5)
        self._moldura_caixa(pdf, 12, ph - 70, gw, 22, localization.label("observacoes_mes"))
        self._linhas(pdf, 12, ph - 70, gw, 22, intervalo=5)

        gy = 8
        grid_top = ph - 76
        gh = grid_top - gy
        pdf.setStrokeColor(COR_LINHA_FORTE)
        pdf.setLineWidth(0.3)
        pdf.rect(sx(gx * mm), sy(gy * mm), sx(gw * mm), sy(gh * mm), fill=0, stroke=1)

        col_w = gw / 7
        header_h = 7
        for d in range(7):
            pdf.setFillColor(COR_NAVY)
            pdf.rect(sx((gx + d * col_w) * mm), sy((grid_top - header_h) * mm),
                     sx(col_w * mm), sy(header_h * mm), fill=1, stroke=0)
            pdf.setFont(_FONT_B, 5.5)
            pdf.setFillColor(COR_BRANCO)
            pdf.drawCentredString(sx((gx + d * col_w + col_w / 2) * mm),
                                  sy((grid_top - header_h + 2.2) * mm), dias_curto[d])

        row_h = (gh - header_h) / max(len(cal), 1)
        for wi, week in enumerate(cal):
            for di, day in enumerate(week):
                if day != 0:
                    dx = gx + di * col_w
                    cell_top = grid_top - header_h - wi * row_h
                    cor_dia = COR_GOLD if di == 6 else COR_NAVY
                    box_x = dx + 1.5
                    box_s = 12
                    pdf.setStrokeColor(cor_dia)
                    pdf.setLineWidth(0.35)
                    pdf.rect(sx(box_x * mm), sy((cell_top - 16) * mm),
                             sx(box_s * mm), sy(box_s * mm), fill=0, stroke=1)
                    pdf.setFont(_FONT_B, 7)
                    pdf.setFillColor(cor_dia)
                    pdf.drawCentredString(sx((box_x + box_s / 2) * mm),
                                          sy((cell_top - 6.5) * mm), str(day))

        pdf.showPage()

    # ------------------------------------------------------------ semanal
    def pagina_semanal(self, pdf, data_segunda):
        self.fundo_pagina(pdf)
        self._borda_pagina(pdf)
        pw = config.LARGURA / mm
        ph = config.ALTURA / mm

        segunda = data_segunda - timedelta(days=data_segunda.weekday())
        domingo = segunda + timedelta(days=6)
        inicio_ano = date(data_segunda.year, 1, 1)
        primeira_segunda = inicio_ano - timedelta(days=inicio_ano.weekday())
        n_semana = ((segunda - primeira_segunda).days // 7) + 1
        titulo = (localization.label("semana_intervalo") %
                  (n_semana, segunda.day, segunda.month, domingo.day, domingo.month, domingo.year))
        self._faixa_titulo(pdf, 8, ph - 16, pw - 16, 11, titulo)

        dias_curto = localization._idioma_atual.get(
            'dias_semana_abr', ['SEG', 'TER', 'QUA', 'QUI', 'SEX', 'SAB', 'DOM'])
        gx = 8
        gw = pw - 16
        col_w = gw / 7

        grid_top = ph - 34
        grid_h = 64
        header_h = 8
        gy = grid_top - grid_h

        for d in range(7):
            dia_data = segunda + timedelta(days=d)
            cx = gx + d * col_w
            pdf.setFillColor(COR_NAVY)
            pdf.rect(sx(cx * mm), sy((grid_top - header_h) * mm),
                     sx(col_w * mm), sy(header_h * mm), fill=1, stroke=0)
            pdf.setFont(_FONT_B, 5.5)
            pdf.setFillColor(COR_BRANCO)
            pdf.drawCentredString(sx((cx + col_w / 2) * mm),
                                  sy((grid_top - header_h + 2.2) * mm),
                                  dias_curto[d] + " " + str(dia_data.day))
            pdf.setStrokeColor(COR_LINHA)
            pdf.setLineWidth(0.15)
            for i in range(int((grid_h - header_h) / 5)):
                ly = grid_top - header_h - (i + 1) * 5
                pdf.line(sx(cx * mm), sy(ly * mm), sx((cx + col_w) * mm), sy(ly * mm))

        prior_y = gy - 12
        self._moldura_caixa(pdf, 8, prior_y, gw, 11, localization.label("prioridades_semana"))
        pdf.setFillColor(COR_NAVY)
        pdf.circle(sx(13 * mm), sy((prior_y + 2.5) * mm), 1.0 * mm, fill=1, stroke=0)
        pdf.setFillColor(COR_GOLD)
        pdf.circle(sx(24 * mm), sy((prior_y + 2.5) * mm), 1.0 * mm, fill=1, stroke=0)
        pdf.setFillColor(COR_NAVY_CLARO)
        pdf.circle(sx(35 * mm), sy((prior_y + 2.5) * mm), 1.0 * mm, fill=1, stroke=0)

        comp_y = 9
        comp_h = prior_y - 12 - comp_y
        self._moldura_caixa(pdf, 8, comp_y, gw, comp_h, localization.label("compromissos_semana"))
        self._linhas(pdf, 8, comp_y, gw, comp_h, intervalo=6)
        pdf.showPage()

    # ------------------------------------------------------------ diario
    def pagina_diaria(self, pdf, data, com_agendamentos=False, maxima=None):
        self.fundo_pagina(pdf)
        self._borda_pagina(pdf)
        pw = config.LARGURA / mm
        ph = config.ALTURA / mm

        # cabecalho
        pdf.setFillColor(COR_NAVY)
        pdf.rect(sx(8 * mm), sy((ph - 24) * mm), sx((pw - 16) * mm), sy(16 * mm), fill=1, stroke=0)
        pdf.setFillColor(COR_GOLD)
        pdf.rect(sx(8 * mm), sy((ph - 24) * mm), sx(2.2 * mm), sy(16 * mm), fill=1, stroke=0)
        pdf.setFont(_FONT_B, 30)
        pdf.setFillColor(COR_BRANCO)
        pdf.drawString(sx(15 * mm), sy((ph - 19) * mm), data.strftime("%d"))
        pdf.setFont(_FONT_B, 10)
        pdf.setFillColor(COR_GOLD_CLARO)
        pdf.drawString(sx(33 * mm), sy((ph - 16) * mm), localization.nome_dia(data).upper())
        pdf.setFont(_FONT, 7)
        pdf.setFillColor(COR_TEXTO_CABECALHO)
        pdf.drawString(sx(33 * mm), sy((ph - 21.5) * mm), data.strftime("%d/%m/%Y"))
        pdf.setFont(_FONT, 6.5)
        pdf.setFillColor(COR_TEXTO_CABECALHO)
        pdf.drawRightString(sx((pw - 12) * mm), sy((ph - 15) * mm),
                            localization.nome_mes(data.month).upper() + " " + str(data.year))

        # frase de prosperidade do dia
        frase = _frase_do_dia(data)
        pdf.setFont(_FONT_O, 6.5)
        pdf.setFillColor(COR_GOLD)
        pdf.drawCentredString(sx((pw / 2) * mm), sy((ph - 29) * mm), frase[:110])

        # rodape: maxima juridica
        if maxima:
            pdf.setFillColor(COR_CREME)
            pdf.rect(sx(8 * mm), sy(4 * mm), sx((pw - 16) * mm), sy(7.5 * mm), fill=1, stroke=0)
            pdf.setStrokeColor(COR_GOLD)
            pdf.setLineWidth(0.4)
            pdf.rect(sx(8 * mm), sy(4 * mm), sx((pw - 16) * mm), sy(7.5 * mm), fill=0, stroke=1)
            pdf.setFont(_FONT_B, 5.8)
            pdf.setFillColor(COR_NAVY)
            pdf.drawString(sx(11 * mm), sy((6.6) * mm), maxima["texto"][:110])
            pdf.setFont(_FONT, 5.2)
            pdf.setFillColor(COR_TEXTO_SEC)
            pdf.drawString(sx(11 * mm), sy((10.2) * mm), _traducao_maxima(maxima)[:110])

        if com_agendamentos:
            self._moldura_caixa(pdf, 8, ph - 46, gw := (pw - 16), 11,
                                localization.label("compromissos_horarios"))
            slot_h = 7
            sched_y = ph - 133
            sched_h = ph - 46 - 8 - sched_y
            pdf.setStrokeColor(COR_LINHA)
            pdf.setLineWidth(0.2)
            n_slots = int(sched_h / slot_h)
            for i in range(n_slots):
                hora = 8 + i
                slot_y = ph - 46 - 8 - i * slot_h
                pdf.setFont(_FONT_B, 5.5)
                pdf.setFillColor(COR_NAVY)
                pdf.drawString(sx(11 * mm), sy((slot_y - 1.5) * mm), "%02d:00" % hora)
                pdf.setStrokeColor(COR_LINHA)
                pdf.setLineWidth(0.2)
                pdf.line(sx(24 * mm), sy((slot_y - 2) * mm), sx((pw - 12) * mm), sy((slot_y - 2) * mm))

            self._moldura_caixa(pdf, 8, 14, gw, ph - 150, localization.label("prazos_anotacoes"))
            self._linhas(pdf, 8, 14, gw, ph - 150, intervalo=6)
        else:
            self._moldura_caixa(pdf, 8, ph - 46, pw - 16, 12, localization.label("prazos_dia"))
            self._linhas(pdf, 8, ph - 46, pw - 16, 12, intervalo=4)
            self._moldura_caixa(pdf, 8, 14, pw - 16, ph - 60, localization.label("anotacoes_dia"))
            self._linhas(pdf, 8, 14, pw - 16, ph - 60, intervalo=6)

        pdf.showPage()

    # ------------------------------------------------------------ extra
    def pagina_secao(self, pdf, titulo, colunas, num_linhas=22):
        """Pagina generica com cabecalho de colunas e linhas para preenchimento."""
        self.fundo_pagina(pdf)
        self._borda_pagina(pdf)
        pw = config.LARGURA / mm
        ph = config.ALTURA / mm

        self._faixa_titulo(pdf, 8, ph - 16, pw - 16, 11, titulo)

        larguras = [c[1] for c in colunas]
        rotulos = [c[0] for c in colunas]
        total = sum(larguras)
        gx = 8
        gw = pw - 16
        escala = gw / total

        x_atual = gx
        y_top = ph - 24
        header_h = 7
        for i, rotulo in enumerate(rotulos):
            w = larguras[i] * escala
            pdf.setFillColor(COR_NAVY)
            pdf.rect(sx(x_atual * mm), sy((y_top - header_h) * mm), sx(w * mm), sy(header_h * mm), fill=1, stroke=0)
            pdf.setFont(_FONT_B, 6)
            pdf.setFillColor(COR_BRANCO)
            pdf.drawString(sx((x_atual + 1.5) * mm), sy((y_top - header_h + 2) * mm), rotulo)
            x_atual += w

        pdf.setStrokeColor(COR_LINHA_FORTE)
        pdf.setLineWidth(0.3)
        pdf.rect(sx(gx * mm), sy(8 * mm), sx(gw * mm), sy((y_top - header_h - 8) * mm), fill=0, stroke=1)

        for i in range(num_linhas):
            ly = y_top - header_h - 4 - i * 6
            if ly < 12:
                break
            pdf.setStrokeColor(COR_LINHA)
            pdf.setLineWidth(0.2)
            pdf.line(sx((gx + 2) * mm), sy(ly * mm), sx((gx + gw - 2) * mm), sy(ly * mm))

        pdf.showPage()

    def pagina_maximas(self, pdf, maximas):
        self.fundo_pagina(pdf)
        self._borda_pagina(pdf)
        pw = config.LARGURA / mm
        ph = config.ALTURA / mm
        self._faixa_titulo(pdf, 8, ph - 16, pw - 16, 11, localization.label("maximas_juridicas"))

        col_w = (pw - 24) / 2
        gx = 10
        gy = ph - 24
        gh = ph - 34
        y_atual = gy
        for m in maximas:
            if y_atual < 10:
                break
            pdf.setFont(_FONT_B, 6)
            pdf.setFillColor(COR_NAVY)
            pdf.drawString(sx(gx * mm), sy(y_atual * mm), m["texto"][:90])
            pdf.setFont(_FONT, 5)
            pdf.setFillColor(COR_TEXTO_SEC)
            pdf.drawString(sx(gx * mm), sy((y_atual - 2.8) * mm), _traducao_maxima(m)[:100])
            pdf.setStrokeColor(COR_LINHA)
            pdf.setLineWidth(0.15)
            pdf.line(sx(gx * mm), sy((y_atual - 4) * mm), sx((gx + col_w) * mm), sy((y_atual - 4) * mm))
            y_atual -= 8.5

        pdf.showPage()


estilo = Juridico()
