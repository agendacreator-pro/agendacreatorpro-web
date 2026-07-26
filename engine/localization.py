IDIOMAS = {
    "pt": {
        "nome": "Portugues",
        "dias_semana": {
            "Monday": "Segunda-feira", "Tuesday": "Terca-feira",
            "Wednesday": "Quarta-feira", "Thursday": "Quinta-feira",
            "Friday": "Sexta-feira", "Saturday": "Sabado", "Sunday": "Domingo"
        },
        "dias_semana_curto": ["S", "T", "Q", "Q", "S", "S", "D"],
        "meses": {
            1: "Janeiro", 2: "Fevereiro", 3: "Marco", 4: "Abril",
            5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
            9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
        },
        "meses_curto": ["JAN", "FEV", "MAR", "ABR", "MAI", "JUN", "JUL", "AGO", "SET", "OUT", "NOV", "DEZ"],
        "feriados": {
            (1, 1): "Confraternizacao Universal",
            (4, 21): "Tiradentes",
            (5, 1): "Dia do Trabalhador",
            (9, 7): "Independencia do Brasil",
            (10, 12): "Nossa Senhora Aparecida",
            (11, 2): "Finados",
            (11, 15): "Proclamacao da Republica",
            (12, 25): "Natal"
        },
        "feriados_moveis": {
            "sexta_feira_santa": "Sexta-feira Santa",
            "pascoa": "Pascoa",
            "corpus_christi": "Corpus Christi"
        },
        "labels": {
            "prioridades": "PRIORIDADES",
            "agendamentos": "AGENDAMENTOS",
            "anotacoes": "ANOTACOES",
            "dados_pessoais": "DADOS PESSOAIS",
            "planejamento": "PLANEJAMENTO",
            "metas": "Metas",
            "projetos": "Projetos",
            "financeiro": "Financeiro",
            "saude": "Saude",
            "estudos": "Estudos",
            "viagens": "Viagens",
            "agenda": "Agenda",
            "planejamento_semanal": "PLANEJAMENTO SEMANAL",
        }
    },
    "en": {
        "nome": "English",
        "dias_semana": {
            "Monday": "Monday", "Tuesday": "Tuesday",
            "Wednesday": "Wednesday", "Thursday": "Thursday",
            "Friday": "Friday", "Saturday": "Saturday", "Sunday": "Sunday"
        },
        "dias_semana_curto": ["M", "T", "W", "T", "F", "S", "S"],
        "meses": {
            1: "January", 2: "February", 3: "March", 4: "April",
            5: "May", 6: "June", 7: "July", 8: "August",
            9: "September", 10: "October", 11: "November", 12: "December"
        },
        "meses_curto": ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"],
        "feriados": {
            (1, 1): "New Year's Day",
            (4, 21): "Tiradentes",
            (5, 1): "Labor Day",
            (9, 7): "Independence Day",
            (10, 12): "Our Lady of Aparecida",
            (11, 2): "All Souls' Day",
            (11, 15): "Republic Day",
            (12, 25): "Christmas"
        },
        "feriados_moveis": {
            "sexta_feira_santa": "Good Friday",
            "pascoa": "Easter",
            "corpus_christi": "Corpus Christi"
        },
        "labels": {
            "prioridades": "PRIORITIES",
            "agendamentos": "SCHEDULE",
            "anotacoes": "NOTES",
            "dados_pessoais": "PERSONAL DATA",
            "planejamento": "PLANNING",
            "metas": "Goals",
            "projetos": "Projects",
            "financeiro": "Finance",
            "saude": "Health",
            "estudos": "Studies",
            "viagens": "Travel",
            "agenda": "Planner",
            "planejamento_semanal": "WEEKLY PLANNING",
        }
    },
    "es": {
        "nome": "Espanhol",
        "dias_semana": {
            "Monday": "Lunes", "Tuesday": "Martes",
            "Wednesday": "Miercoles", "Thursday": "Jueves",
            "Friday": "Viernes", "Saturday": "Sabado", "Sunday": "Domingo"
        },
        "dias_semana_curto": ["L", "M", "X", "J", "V", "S", "D"],
        "meses": {
            1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
            5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
            9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
        },
        "meses_curto": ["ENE", "FEB", "MAR", "ABR", "MAY", "JUN", "JUL", "AGO", "SEP", "OCT", "NOV", "DIC"],
        "feriados": {
            (1, 1): "Año Nuevo",
            (4, 21): "Tiradentes",
            (5, 1): "Dia del Trabajo",
            (9, 7): "Dia de la Independencia",
            (10, 12): "Nuestra Señora de Aparecida",
            (11, 2): "Dia de los Fieles Difuntos",
            (11, 15): "Proclamación de la República",
            (12, 25): "Navidad"
        },
        "feriados_moveis": {
            "sexta_feira_santa": "Viernes Santo",
            "pascoa": "Pascua",
            "corpus_christi": "Corpus Christi"
        },
        "labels": {
            "prioridades": "PRIORIDADES",
            "agendamentos": "CITAS",
            "anotacoes": "NOTAS",
            "dados_pessoais": "DATOS PERSONALES",
            "planejamento": "PLANIFICACION",
            "metas": "Metas",
            "projetos": "Proyectos",
            "financeiro": "Finanzas",
            "saude": "Salud",
            "estudos": "Estudios",
            "viagens": "Viajes",
            "agenda": "Agenda",
            "planejamento_semanal": "PLANIFICACION SEMANAL",
        }
    }
}

_idioma_atual = IDIOMAS["pt"]


def definir_idioma(codigo):
    global _idioma_atual
    _idioma_atual = IDIOMAS.get(codigo, IDIOMAS["pt"])


def obter_idioma():
    return _idioma_atual


def nome_mes(numero):
    return _idioma_atual["meses"].get(numero, "")


def nome_mes_curto(numero):
    idx = numero - 1
    if 0 <= idx < len(_idioma_atual["meses_curto"]):
        return _idioma_atual["meses_curto"][idx]
    return ""


def nome_dia(data):
    return _idioma_atual["dias_semana"].get(data.strftime("%A"), "")


def nome_dia_semana(idx):
    if 0 <= idx < len(_idioma_atual["dias_semana_curto"]):
        return _idioma_atual["dias_semana_curto"][idx]
    return ""


def obter_feriado(data):
    fixo = _idioma_atual["feriados"].get((data.month, data.day), "")
    if fixo:
        return fixo
    from calendar_engine import _pascoa, _feriados_moveis_br
    moveis = _feriados_moveis_br(data.year)
    traducoes = _idioma_atual["feriados_moveis"]
    br_key_map = {
        "Sexta-feira Santa": "sexta_feira_santa",
        "Pascoa": "pascoa",
        "Corpus Christi": "corpus_christi"
    }
    feriado_br = moveis.get(data, "")
    if feriado_br:
        key = br_key_map.get(feriado_br, "")
        return traducoes.get(key, feriado_br)
    return ""


def label(nome):
    return _idioma_atual["labels"].get(nome, nome)
