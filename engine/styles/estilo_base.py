import math
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import config
from config import sx, sy
from colors import *
import themes
import localization


_FONT_B = "Helvetica-Bold"
_FONT = "Helvetica"


class EstiloBase:
    nome = "Base"
    _decorations_drawn = set()

    def _theme_accent(self):
        t = themes.tema_atual
        return t.titulo

    def _theme_accent_dark(self):
        t = themes.tema_atual
        return t.importante

    def _theme_tasks(self):
        t = themes.tema_atual
        return t.tarefas

    def _theme_destaque(self):
        t = themes.tema_atual
        return t.destaque

    def _theme_text(self):
        t = themes.tema_atual
        return t.texto

    def _cor(self, nome_attr, fallback=PRETO):
        return getattr(self, nome_attr, fallback)

    def _hex(self, hex_str):
        return HexColor(hex_str)

    def _font(self, negrito=False, tamanho=10):
        return _FONT_B if negrito else _FONT

    def _mm(self, v):
        return v * mm

    def _sx(self, v):
        return sx(v * mm)

    def _sy(self, v):
        return sy(v * mm)

    def fundo_pagina(self, pdf):
        pdf.setFillColor(BRANCO)
        pdf.rect(0, 0, config.LARGURA, config.ALTURA, fill=1, stroke=0)

    def cabecalho_diario(self, pdf, data, x, y, w, h):
        pdf.setFillColor(self._theme_accent())
        pdf.rect(sx(x * mm), sy(y * mm), sx(w * mm), sy(h * mm), fill=1, stroke=0)
        pdf.setFillColor(BRANCO)
        pdf.setFont(_FONT_B, 20)
        pdf.drawString(sx((x + 2) * mm), sy((y + 3) * mm), str(data.day).zfill(2))
        pdf.setFont(_FONT, 7)
        nomes_mes = [
            "JANEIRO", "FEVEREIRO", "MARCO", "ABRIL",
            "MAIO", "JUNHO", "JULHO", "AGOSTO",
            "SETEMBRO", "OUTUBRO", "NOVEMBRO", "DEZEMBRO"
        ]
        pdf.drawString(sx((x + 2) * mm), sy((y + 1) * mm), nomes_mes[data.month - 1] + " " + str(data.year))
        nomes_dia = ["SEGUNDA", "TERCA", "QUARTA", "QUINTA", "SEXTA", "SABADO", "DOMINGO"]
        pdf.drawString(sx((x + 20) * mm), sy((y + 3) * mm), nomes_dia[data.weekday()])

    def faixa_mes(self, pdf, x, y, w, h, data):
        pdf.setFillColor(self._theme_accent())
        pdf.rect(sx(x * mm), sy(y * mm), sx(w * mm), sy(h * mm), fill=1, stroke=0)
        pdf.setFillColor(BRANCO)
        pdf.setFont(_FONT_B, 10)
        pdf.drawString(sx((x + 1) * mm), sy((y + 1) * mm), localization.nome_mes(data.month))

    def caixa_prioridades(self, pdf, x, y, w, h):
        pdf.setFillColor(self._theme_tasks())
        pdf.rect(sx(x * mm), sy(y * mm), sx(w * mm), sy(h * mm), fill=1, stroke=0)
        pdf.setFillColor(BRANCO)
        pdf.setFont(_FONT_B, 10)
        pdf.drawString(sx((x + 1) * mm), sy((y + 1) * mm), localization.label("prioridades"))

    def area_anotacoes(self, pdf, x, y, w, h, num_linhas=8, com_agendamentos=False):
        pdf.setFillColor(HexColor("#F8F8F8"))
        pdf.rect(sx(x * mm), sy(y * mm), sx(w * mm), sy(h * mm), fill=1, stroke=0)

        if com_agendamentos:
            notes_w = w * 0.65
            sched_x = x + notes_w + 2
            sched_w = w - notes_w - 2

            pdf.setStrokeColor(LINHA)
            pdf.setLineWidth(0.3)
            pdf.line(sx(sched_x * mm), sy((y + h) * mm), sx(sched_x * mm), sy(y * mm))

            pdf.setFont(_FONT_B, 7)
            pdf.setFillColor(self._theme_accent())
            pdf.drawString(sx((sched_x + 1) * mm), sy((y + h - 5) * mm), localization.label("agendamentos"))

            pdf.setFont(_FONT, 6)
            pdf.setFillColor(self._theme_text())
            slot_h = (h - 8) / 11
            for i in range(11):
                hora = 8 + i
                slot_y = y + h - 9.5 - i * slot_h
                pdf.setFont(_FONT_B, 5.5)
                pdf.setFillColor(self._theme_accent())
                pdf.drawString(sx((sched_x + 1) * mm), sy((slot_y - 1) * mm), f"{hora:02d}:00")
                pdf.setStrokeColor(LINHA)
                pdf.setLineWidth(0.2)
                pdf.line(sx((sched_x + 12) * mm), sy((slot_y - 1.5) * mm), sx((x + w - 1) * mm), sy((slot_y - 1.5) * mm))

            full_num_linhas = max(3, int((h - 8) / 5))
            linha_y = y + h - 8
            pdf.setStrokeColor(LINHA)
            pdf.setLineWidth(0.3)
            for i in range(full_num_linhas):
                ly = linha_y - i * 5
                if ly < y + 4:
                    break
                pdf.line(sx((x + 2) * mm), sy(ly * mm), sx((sched_x - 2) * mm), sy(ly * mm))
        else:
            pdf.setStrokeColor(LINHA)
            pdf.setLineWidth(0.5)
            linha_y = y + h - 8
            for i in range(num_linhas):
                if linha_y - i * 5 < y:
                    break
                pdf.line(sx(x * mm), sy((linha_y - i * 5) * mm),
                         sx((x + w) * mm), sy((linha_y - i * 5) * mm))

    def caixa_agendamentos(self, pdf, x, y, w, h):
        pdf.setFillColor(HexColor("#F8F8F8"))
        pdf.rect(sx(x * mm), sy(y * mm), sx(w * mm), sy(h * mm), fill=1, stroke=0)
        pdf.setFillColor(self._theme_tasks())
        pdf.rect(sx(x * mm), sy((y + h - 7) * mm), sx(w * mm), sy(7 * mm), fill=1, stroke=0)
        pdf.setFillColor(BRANCO)
        pdf.setFont(_FONT_B, 8)
        pdf.drawString(sx((x + 1) * mm), sy((y + h - 5.5) * mm), localization.label("agendamentos"))
        slot_h = (h - 9) / 14
        pdf.setFont(_FONT, 6)
        pdf.setFillColor(self._theme_text())
        pdf.setStrokeColor(LINHA)
        pdf.setLineWidth(0.3)
        for i in range(14):
            hora = 7 + i
            slot_y = y + h - 9 - (i + 1) * slot_h
            pdf.setFillColor(self._theme_accent())
            pdf.setFont(_FONT_B, 6)
            pdf.drawString(sx((x + 1) * mm), sy((slot_y + 1) * mm), f"{hora:02d}:00")
            pdf.setStrokeColor(LINHA)
            pdf.setLineWidth(0.3)
            pdf.line(sx((x + 14) * mm), sy((slot_y + 0.5) * mm), sx((x + w - 1) * mm), sy((slot_y + 0.5) * mm))

    def divisor(self, pdf, x1, y, x2):
        pdf.setStrokeColor(self._theme_accent())
        pdf.setLineWidth(0.5)
        pdf.line(sx(x1 * mm), sy(y * mm), sx(x2 * mm), sy(y * mm))

    def pagina_dados_pessoais(self, pdf, campos):
        self.fundo_pagina(pdf)
        pdf.setFillColor(self._theme_accent())
        pdf.rect(sx(0), sy(200 * mm), sx(config.LARGURA), sy(30 * mm), fill=1, stroke=0)
        pdf.setFillColor(BRANCO)
        pdf.setFont(_FONT_B, 14)
        pdf.drawString(sx(15 * mm), sy(205 * mm), localization.label("dados_pessoais"))
        y = 185
        pdf.setFillColor(PRETO)
        for campo in campos:
            pdf.setFont(_FONT_B, 8)
            pdf.drawString(sx(15 * mm), sy(y * mm), campo + ":")
            pdf.setStrokeColor(self._theme_accent())
            pdf.setLineWidth(0.5)
            pdf.line(sx(40 * mm), sy((y - 1) * mm), sx(120 * mm), sy((y - 1) * mm))
            y -= 15
        pdf.showPage()

    def planejamento(self, pdf, caixas):
        self.fundo_pagina(pdf)
        pdf.setFillColor(self._theme_accent())
        pdf.rect(sx(0), sy(200 * mm), sx(config.LARGURA), sy(30 * mm), fill=1, stroke=0)
        pdf.setFillColor(BRANCO)
        pdf.setFont(_FONT_B, 14)
        pdf.drawString(sx(15 * mm), sy(205 * mm), localization.label("planejamento"))
        for titulo, y, num_linhas in caixas:
            pdf.setFillColor(self._theme_tasks())
            pdf.rect(sx(10 * mm), sy((y + 4) * mm), sx(120 * mm), sy(6 * mm), fill=1, stroke=0)
            pdf.setFillColor(BRANCO)
            pdf.setFont(_FONT_B, 8)
            pdf.drawString(sx(12 * mm), sy((y + 5) * mm), titulo)
            pdf.setStrokeColor(self._theme_accent())
            pdf.setLineWidth(0.3)
            for i in range(num_linhas):
                pdf.line(sx(10 * mm), sy((y - i * 3.5) * mm), sx(130 * mm), sy((y - i * 3.5) * mm))
        pdf.showPage()

    def pagina_semanal_titulo(self, pdf):
        self.fundo_pagina(pdf)
        pdf.setFillColor(self._theme_accent())
        pdf.rect(sx(0), sy(200 * mm), sx(config.LARGURA), sy(30 * mm), fill=1, stroke=0)

    def pagina_semanal_dias(self, pdf, dias_info):
        x = 10
        y = 155
        w = 50
        h = 40
        for i, (dia, mes, nome_dia) in enumerate(dias_info):
            col = i % 2
            lin = i // 2
            px = x + col * 65
            py = y - lin * 48
            pdf.setFillColor(self._theme_accent())
            pdf.rect(sx(px * mm), sy(py * mm), sx(w * mm), sy(h * mm), fill=1, stroke=0)
            pdf.setFillColor(BRANCO)
            pdf.setFont(_FONT_B, 10)
            pdf.drawString(sx((px + 2) * mm), sy((py + 1) * mm), f"{dia}/{mes}")
            pdf.setFont(_FONT, 8)
            pdf.drawString(sx((px + 2) * mm), sy((py - 3) * mm), nome_dia)
            pdf.setStrokeColor(LINHA)
            pdf.setLineWidth(0.3)
            for j in range(5):
                pdf.line(sx((px + 1) * mm), sy((py - 8 - j * 5) * mm),
                         sx((px + w - 1) * mm), sy((py - 8 - j * 5) * mm))

    def pagina_semanal_prioridades(self, pdf, x, y, w, h):
        pdf.setFillColor(self._theme_tasks())
        pdf.rect(sx(x * mm), sy(y * mm), sx(w * mm), sy(h * mm), fill=1, stroke=0)
        pdf.setFillColor(BRANCO)
        pdf.setFont(_FONT_B, 8)
        pdf.drawString(sx((x + 1) * mm), sy((y + 1) * mm), "PRIORIDADES")

    def pagina_semanal_escrita(self, pdf, x, y, w, h):
        pdf.setStrokeColor(LINHA)
        pdf.setLineWidth(0.3)
        num_linhas = int(h / 5)
        for i in range(num_linhas):
            pdf.line(sx(x * mm), sy((y + h - 5 - i * 5) * mm),
                     sx((x + w) * mm), sy((y + h - 5 - i * 5) * mm))

    def decorar_canto(self, pdf, x, y, corner="tl"):
        pdf.setFillColor(self._theme_accent())
        pdf.circle(sx(x * mm), sy(y * mm), sx(1.5 * mm), fill=1, stroke=0)

    def decorar_borda(self, pdf):
        pdf.setStrokeColor(self._theme_accent())
        pdf.setLineWidth(0.5)
        pdf.rect(sx(5 * mm), sy(5 * mm), sx((config.LARGURA / mm - 10) * mm),
                 sy((config.ALTURA / mm - 10) * mm), fill=0, stroke=1)

    def desenhar_logo(self, pdf):
        pdf.setFillColor(self._theme_accent())
        pdf.setFont(_FONT_B, 20)
        pdf.drawString(sx(10 * mm), sy(210 * mm), "AGENDA PRO")

    def pagina_calendario_anual(self, pdf, ano, idioma='pt'):
        import calendar
        self.fundo_pagina(pdf)
        pw_mm = config.LARGURA / mm
        ph_mm = config.ALTURA / mm

        pdf.setFillColor(self._theme_accent())
        pdf.rect(sx(0), sy((ph_mm - 14) * mm), sx(config.LARGURA), sy(14 * mm), fill=1, stroke=0)
        pdf.setFillColor(BRANCO)
        pdf.setFont(_FONT_B, 14)
        pdf.drawCentredString(sx(pw_mm / 2 * mm), sy((ph_mm - 10) * mm), str(ano))

        margin_x = 8
        margin_top = ph_mm - 20
        margin_bottom = 8
        cols = 4
        rows = 3
        gap_x = 4
        gap_y = 5
        cell_w = (pw_mm - 2 * margin_x - (cols - 1) * gap_x) / cols
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

            pdf.setFillColor(BRANCO)
            pdf.setStrokeColor(self._theme_accent())
            pdf.setLineWidth(0.3)
            pdf.rect(sx(cx * mm), sy(cy * mm), sx(cell_w * mm), sy(cell_h * mm), fill=1, stroke=1)

            pdf.setFillColor(self._theme_accent())
            pdf.rect(sx(cx * mm), sy((cy + cell_h - 7) * mm), sx(cell_w * mm), sy(7 * mm), fill=1, stroke=0)
            pdf.setFillColor(BRANCO)
            pdf.setFont(_FONT_B, 6)
            pdf.drawCentredString(sx((cx + cell_w / 2) * mm), sy((cy + cell_h - 5.5) * mm), meses[mes].upper())

            day_label_y = cy + cell_h - 12
            day_w = cell_w / 7
            pdf.setFillColor(self._theme_accent())
            pdf.setFont(_FONT_B, 4.5)
            for d in range(7):
                dx = cx + d * day_w + day_w / 2
                pdf.drawCentredString(sx(dx * mm), sy(day_label_y * mm), dias_curto[d])

            cal = calendar.monthcalendar(ano, mes)
            start_y = day_label_y - 4
            row_h = (start_y - cy - 2) / max(len(cal), 1)
            for wi, week in enumerate(cal):
                for di, day in enumerate(week):
                    if day != 0:
                        dx = cx + di * day_w + day_w / 2
                        dy = start_y - wi * row_h
                        if di == 6:
                            pdf.setFillColor(HexColor("#CC0000"))
                        else:
                            pdf.setFillColor(self._theme_destaque())
                        pdf.setFont(_FONT, 4.5)
                        pdf.drawCentredString(sx(dx * mm), sy(dy * mm), str(day))

        pdf.showPage()
