from datetime import date, timedelta

MESES = {
    1: "Janeiro", 2: "Fevereiro", 3: "Marco", 4: "Abril",
    5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
    9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
}

DIAS = {
    "Monday": "Segunda-feira", "Tuesday": "Terca-feira",
    "Wednesday": "Quarta-feira", "Thursday": "Quinta-feira",
    "Friday": "Sexta-feira", "Saturday": "Sabado", "Sunday": "Domingo"
}

FERIADOS_FIXOS = {
    (1, 1): "Confraternizacao Universal",
    (4, 21): "Tiradentes",
    (5, 1): "Dia do Trabalhador",
    (9, 7): "Independencia do Brasil",
    (10, 12): "Nossa Senhora Aparecida",
    (11, 2): "Finados",
    (11, 15): "Proclamacao da Republica",
    (12, 25): "Natal"
}


def _pascoa(ano):
    a = ano % 19
    b = ano // 100
    c = ano % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    mes = (h + l - 7 * m + 114) // 31
    dia = ((h + l - 7 * m + 114) % 31) + 1
    return date(ano, mes, dia)


def _feriados_moveis_br(ano):
    pascoa = _pascoa(ano)
    return {
        pascoa - timedelta(days=2): "Sexta-feira Santa",
        pascoa: "Pascoa",
        pascoa + timedelta(days=60): "Corpus Christi",
    }


def obter_feriado(data):
    fixo = FERIADOS_FIXOS.get((data.month, data.day), "")
    if fixo:
        return fixo
    moveis = _feriados_moveis_br(data.year)
    return moveis.get(data, "")


def nome_mes(numero):
    return MESES.get(numero, "")


def nome_dia(data):
    return DIAS.get(data.strftime("%A"), "")


def ano_bissexto(ano):
    return (ano % 400 == 0 or (ano % 4 == 0 and ano % 100 != 0))
