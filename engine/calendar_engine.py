from datetime import date

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

FERIADOS = {
    (1, 1): "Confraternizacao Universal",
    (4, 21): "Tiradentes",
    (5, 1): "Dia do Trabalhador",
    (9, 7): "Independencia do Brasil",
    (10, 12): "Nossa Senhora Aparecida",
    (11, 2): "Finados",
    (11, 15): "Proclamacao da Republica",
    (12, 25): "Natal"
}

def nome_mes(numero):
    return MESES.get(numero, "")

def nome_dia(data):
    return DIAS.get(data.strftime("%A"), "")

def obter_feriado(data):
    return FERIADOS.get((data.month, data.day), "")

def ano_bissexto(ano):
    return (ano % 400 == 0 or (ano % 4 == 0 and ano % 100 != 0))
