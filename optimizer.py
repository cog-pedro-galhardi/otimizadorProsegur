from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional
from datetime import date
import calendar
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta
from mip import Model, xsum, minimize, BINARY, INTEGER, OptimizationStatus
from time import time
import pandas as pd
import numpy as np


def listar_datas_mes(ano: int, mes: int):
    # Obtém o número de dias no mês e ano informados
    num_dias = calendar.monthrange(ano, mes)[1]

    # Cria uma lista com todas as datas no formato 'YYYY-MM-DD'
    datas = [
        datetime(ano, mes, dia).strftime("%Y-%m-%d") for dia in range(1, num_dias + 1)
    ]

    return datas


def gerar_lista_datas(data_inicio: str, data_fim: str):
    # Converte as strings de data para objetos datetime
    data_inicio = datetime.strptime(data_inicio, "%Y-%m-%d")
    data_fim = datetime.strptime(data_fim, "%Y-%m-%d")

    # Inicializa a lista de datas
    lista_datas = []

    # Percorre o intervalo de datas
    while data_inicio <= data_fim:
        # Adiciona a data atual à lista no formato de texto
        lista_datas.append(data_inicio.strftime("%Y-%m-%d"))
        # Incrementa a data em um dia
        data_inicio += timedelta(days=1)

    return lista_datas


def listar_dias_da_semana_mes(data_inicio: str, data_fim: str):
    data_inicio = datetime.strptime(data_inicio, "%Y-%m-%d")
    data_fim = datetime.strptime(data_fim, "%Y-%m-%d")

    # Inicializa a lista de datas
    lista_datas = []

    # Percorre o intervalo de datas
    while data_inicio <= data_fim:
        # Adiciona a data atual à lista no formato de texto
        lista_datas.append(data_inicio.strftime("%A"))
        # Incrementa a data em um dia
        data_inicio += timedelta(days=1)

    return lista_datas


def gerar_lista_meses(inicio_mes, inicio_ano, fim_mes, fim_ano):
    # Criar data inicial e final
    data_inicio = datetime(inicio_ano, inicio_mes, 1)
    data_fim = datetime(fim_ano, fim_mes, 1)

    # Lista para armazenar os meses
    lista_meses = []

    # Iterar sobre os meses no intervalo
    while data_inicio <= data_fim:
        lista_meses.append(data_inicio.strftime("%Y-%m"))
        data_inicio += relativedelta(months=1)  # Avançar para o próximo mês

    return lista_meses


def jornada_6_por_1_sab_4(data_inicio: str, data_fim: str):
    dias_semana = listar_dias_da_semana_mes(data_inicio, data_fim)
    return [
        8 if value not in ["Saturday", "Sunday"] else (4 if value == "Saturday" else 0)
        for value in dias_semana
    ]


def jornada_6_por_1(data_inicio: str, data_fim: str):
    dias_semana = listar_dias_da_semana_mes(data_inicio, data_fim)
    return [7 + 20 / 60 if value not in ["Sunday"] else 0 for value in dias_semana]


def jornada_5_por_2(data_inicio: str, data_fim: str):

    dias_semana = listar_dias_da_semana_mes(data_inicio, data_fim)
    return [
        8 + 40 / 60 if value not in ["Saturday", "Sunday"] else 0
        for value in dias_semana
    ]


def jornada_12_36_par(data_inicio: str, data_fim: str):
    num_dias = len(listar_dias_da_semana_mes(data_inicio, data_fim))
    return [12 if (i + 1) % 2 == 0 else 0 for i in range(num_dias)]


def jornada_12_36_impar(data_inicio: str, data_fim: str):
    num_dias = len(listar_dias_da_semana_mes(data_inicio, data_fim))
    return [0 if (i + 1) % 2 == 0 else 12 for i in range(num_dias)]


def dias_uteis_5_por_2(data_inicio: str, data_fim: str):

    dias_semana = listar_dias_da_semana_mes(data_inicio, data_fim)
    return [0 if value in ["Saturday", "Sunday"] else 1 for value in dias_semana]


def dias_uteis_6_por_1(data_inicio: str, data_fim: str):
    dias_semana = listar_dias_da_semana_mes(data_inicio, data_fim)
    return [0 if value in ["Sunday"] else 1 for value in dias_semana]


def dias_uteis_12_36_par(data_inicio: str, data_fim: str):
    num_dias = len(listar_dias_da_semana_mes(data_inicio, data_fim))
    return [1 if (i + 1) % 2 == 0 else 0 for i in range(num_dias)]


def dias_uteis_12_36_impar(data_inicio: str, data_fim: str):
    num_dias = len(listar_dias_da_semana_mes(data_inicio, data_fim))
    return [0 if (i + 1) % 2 == 0 else 1 for i in range(num_dias)]


funcoes_escala = {
    "5X2": dias_uteis_5_por_2,
    "6X1": dias_uteis_6_por_1,
    "12X36 Folga PAR": dias_uteis_12_36_impar,
    "12X36 Folga IMPAR": dias_uteis_12_36_par,
}


def zero_or_positive(value: float) -> float:
    if value < 0:
        return 0
    return value


def div_or_zero(a: float, b: float) -> float:
    try:
        return a / b
    except ZeroDivisionError:
        return 0.0


class OtimizadorEscalas:

    def __init__(
        self,
        data_inicio: str,
        data_fim: str,
        FUNCIONARIOS: Dict[int, str],
        FUNCIONARIOS_FERIAS: Dict[int, str],
        FUNCIONARIOS_TREINAMENTO: Dict[int, str],
        FUNCOES: Dict[int, str],
        FUNCAO_FUNCIONARIO: Dict[int, str],
        ESCALAS: Dict[int, str],
        JORNADAS: Dict[int, str],
        DIAS_FUNCOES_JORNADAS: List[Tuple[int, int, int]],
        p_demanda: Dict[Tuple[int, int, int], int],
        p_dias_ativos_funcionario: Dict[Tuple[int, int], int],
        p_vagas_treinamento: Dict[int, int],
        p_duracao_ferias: Dict[int, int],
        p_escala_duracao_jornada_horas: Dict[Tuple[int, int], float],
        p_duracao_jornada_horas: Dict[int, int],
        p_escala_duracao_hora_extra: Dict[int, int],
        cod_filial: Optional[int] = None,
    ) -> None:
        self.data_inicio = data_inicio
        self.data_fim = data_fim
        self.cod_filial = cod_filial
        self.DIAS = {
            i: data for i, data in enumerate(gerar_lista_datas(data_inicio, data_fim))
        }
        self.FUNCIONARIOS = FUNCIONARIOS
        self.FUNCIONARIOS_FERIAS = FUNCIONARIOS_FERIAS
        self.FUNCIONARIOS_TREINAMENTO = FUNCIONARIOS_TREINAMENTO
        self.FUNCOES = FUNCOES
        self.FUNCAO_FUNCIONARIO = FUNCAO_FUNCIONARIO
        self.ESCALAS = ESCALAS
        self.JORNADAS = JORNADAS
        self.DIAS_FUNCOES_JORNADAS = DIAS_FUNCOES_JORNADAS

        self.p_dias_ativos_escala = {}
        for e in self.ESCALAS:
            for i, value in enumerate(
                funcoes_escala[self.ESCALAS[e]](data_inicio, data_fim)
            ):
                self.p_dias_ativos_escala.setdefault((i, e), value)

        self.p_demanda = p_demanda
        self.p_dias_ativos_funcionario = p_dias_ativos_funcionario
        self.p_vagas_treinamento = p_vagas_treinamento
        self.p_duracao_ferias = p_duracao_ferias
        self.p_escala_duracao_jornada_horas = p_escala_duracao_jornada_horas
        self.p_duracao_jornada_horas = p_duracao_jornada_horas
        self.p_escala_duracao_hora_extra = p_escala_duracao_hora_extra

    def run(
        self,
        max_seconds=None,
        max_mip_gap=None,
        priorizar_ferias=False,
        priorizar_hora_extra=False,
    ):
        self.model = Model()

        # Variáveis
        # 1 caso o funcionário w seja alocado desempenhando a função p no dia d, 0 caso contrário
        self.v_trabalho = [
            [
                [
                    [self.model.add_var(var_type=BINARY) for j in self.JORNADAS]
                    for e in self.ESCALAS
                ]
                for f in self.FUNCIONARIOS
            ]
            for i in self.DIAS
        ]
        # 1 caso o funcionário seja alocado na escala s w, 0 caso contrário
        self.v_escala = [
            [self.model.add_var(var_type=BINARY) for e in self.ESCALAS]
            for f in self.FUNCIONARIOS
        ]
        self.v_treinamento = [
            [self.model.add_var(var_type=BINARY) for f in self.FUNCIONARIOS_FERIAS]
            for i in self.DIAS
        ]
        self.v_inicio_ferias = [
            [self.model.add_var(var_type=BINARY) for f in self.FUNCIONARIOS_FERIAS]
            for i in self.DIAS
        ]
        self.v_alpha = [
            [self.model.add_var(var_type=INTEGER) for p in self.FUNCOES]
            for i in self.DIAS
        ]
        self.v_hora_extra = [
            [self.model.add_var(var_type=BINARY) for f in self.FUNCIONARIOS]
            for i in self.DIAS
        ]
        self.v_hora_extra_extra = [
            [self.model.add_var(var_type=INTEGER) for f in self.FUNCIONARIOS]
            for i in self.DIAS
        ]

        # Objetivo
        self.model.objective = minimize(
            (100000 if not priorizar_hora_extra else 1)
            * xsum(self.v_alpha[i][p] for i in self.DIAS for p in self.FUNCOES)
            - (
                xsum(
                    self.v_inicio_ferias[i][f]
                    * min(len(self.DIAS) - i, self.p_duracao_ferias[f])
                    for i in self.DIAS
                    for f in self.FUNCIONARIOS_FERIAS
                )
                + xsum(
                    self.v_treinamento[i][f]
                    for i in self.DIAS
                    for f in self.FUNCIONARIOS_TREINAMENTO
                )
            )
            + xsum(
                self.p_demanda[i, p, j]
                * (
                    self.v_trabalho[i][f][e][j]
                    * (
                        self.p_escala_duracao_jornada_horas[i, e]
                        - self.p_duracao_jornada_horas[j]
                    )
                    + self.v_hora_extra[i][f] * self.p_escala_duracao_hora_extra[e]
                    + self.v_hora_extra_extra[i][f]
                )
                for i in self.DIAS
                for f in self.FUNCIONARIOS
                for p in self.FUNCOES
                for e in self.ESCALAS
                for j in self.JORNADAS
                if (i, p, j) in self.DIAS_FUNCOES_JORNADAS
            )
            # + xsum(
            #     self.p_demanda[i, p, j]
            #     * zero_or_positive(
            #         self.p_duracao_jornada_horas[j]
            #         - self.p_escala_duracao_jornada_horas[i, e]
            #     )
            #     * self.v_trabalho[i][f][e][j]
            #     for i in self.DIAS
            #     for f in self.FUNCIONARIOS
            #     for p in self.FUNCOES
            #     for e in self.ESCALAS
            #     for j in self.JORNADAS
            #     if (i, p, j) in self.DIAS_FUNCOES_JORNADAS
            # )
        )

        # Restrições
        for i, p, j in self.DIAS_FUNCOES_JORNADAS:
            if p != 3:
                self.model += (
                    xsum(
                        self.v_trabalho[i][f][e][j]
                        for f in [
                            index
                            for index, value in self.FUNCAO_FUNCIONARIO.items()
                            if value == p
                        ]
                        for e in self.ESCALAS
                    )
                    + self.v_alpha[i][p]
                    >= self.p_demanda[i, p, j]
                )
            else:
                self.model += (
                    xsum(
                        self.v_trabalho[i][f][e][j]
                        for f in self.FUNCIONARIOS
                        for e in self.ESCALAS
                    )
                    + self.v_alpha[i][p]
                    >= self.p_demanda[i, p, j]
                )

        for f in self.FUNCIONARIOS:
            self.model += xsum(self.v_escala[f][e] for e in self.ESCALAS) == 1

        for i in self.DIAS:
            for f in self.FUNCIONARIOS:
                for e in self.ESCALAS:
                    self.model += (
                        sum(
                            self.v_trabalho[i][f][e][j]
                            for j in self.JORNADAS
                            if (i, self.FUNCAO_FUNCIONARIO[f], j)
                            in self.DIAS_FUNCOES_JORNADAS
                        )
                        <= self.p_dias_ativos_escala[i, e]
                        * self.p_dias_ativos_funcionario[i, f]
                        * self.v_escala[f][e]
                    )

        for i in self.DIAS:
            self.model += xsum(
                self.v_treinamento[i][f] for f in self.FUNCIONARIOS_TREINAMENTO
            ) <= self.p_vagas_treinamento[i] * xsum(
                self.p_dias_ativos_escala[i, e] * self.v_escala[f][e]
                for e in self.ESCALAS
            )

        for f in self.FUNCIONARIOS_FERIAS:
            for i in self.DIAS:
                if i > len(self.DIAS) - self.p_duracao_ferias[f]:
                    self.model += self.v_inicio_ferias[i][f] == 0

        for i in self.DIAS:
            for f in self.FUNCIONARIOS:
                if i == 0:
                    self.model += (
                        self.v_treinamento[i][f] if i in self.FUNCIONARIOS_FERIAS else 0
                    ) + xsum(
                        self.v_trabalho[i][f][e][j]
                        for e in self.ESCALAS
                        for j in self.JORNADAS
                        if (i, self.FUNCAO_FUNCIONARIO[f], j)
                        in self.DIAS_FUNCOES_JORNADAS
                    ) + (
                        self.v_inicio_ferias[i][f]
                        if f in self.FUNCIONARIOS_FERIAS
                        else 0
                    ) <= 1
                else:
                    self.model += (
                        self.v_treinamento[i][f] if i in self.FUNCIONARIOS_FERIAS else 0
                    ) + xsum(
                        self.v_trabalho[i][f][e][j]
                        for e in self.ESCALAS
                        for j in self.JORNADAS
                        if (i, self.FUNCAO_FUNCIONARIO[f], j)
                        in self.DIAS_FUNCOES_JORNADAS
                    ) + (
                        self.v_inicio_ferias[i][f]
                        + sum(
                            self.v_inicio_ferias[_i][f]
                            for _i in range(
                                i - 1, max(i - self.p_duracao_ferias[f], -1), -1
                            )
                        )
                        if f in self.FUNCIONARIOS_FERIAS
                        else 0
                    ) <= 1

        if not priorizar_ferias:
            for f in self.FUNCIONARIOS_FERIAS:
                self.model += xsum(self.v_inicio_ferias[i][f] for i in self.DIAS) <= 1
        else:
            for f in self.FUNCIONARIOS_FERIAS:
                self.model += xsum(self.v_inicio_ferias[i][f] for i in self.DIAS) == 1

        for f in self.FUNCIONARIOS_TREINAMENTO:
            self.model += xsum(self.v_treinamento[i][f] for i in self.DIAS) <= 1

        for f in self.FUNCIONARIOS:
            for i in self.DIAS:
                for e in self.ESCALAS:
                    for j in self.JORNADAS:
                        if (
                            i,
                            self.FUNCAO_FUNCIONARIO[f],
                            j,
                        ) in self.DIAS_FUNCOES_JORNADAS:
                            self.model += (
                                self.v_trabalho[i][f][e][j]
                                * (
                                    self.p_escala_duracao_jornada_horas[i, e]
                                    - self.p_duracao_jornada_horas[j]
                                )
                                + self.v_hora_extra[i][f]
                                * self.p_escala_duracao_hora_extra[e]
                                + self.v_hora_extra_extra[i][f]
                                >= 0
                            )
        for f in self.FUNCIONARIOS:
            for i in self.DIAS:
                self.model += (
                    self.v_hora_extra_extra[i][f] <= 10 * self.v_hora_extra[i][f]
                )

        ref = time()
        if max_mip_gap:
            self.model.max_mip_gap = max_mip_gap
        self.model.verbose = 0
        if max_seconds:
            self.model.max_seconds = max_seconds
        status = self.model.optimize()
        self.optimization_status = status == OptimizationStatus.OPTIMAL
        self.optimization_time = round(time() - ref, 2)
        self.optimization_gap = (
            self.model.objective_value - self.model.objective_bound
        ) / self.model.objective_bound

    def print_solution_report(self):
        print(f"Função objetivo: {self.model.objective_value}")
        print()
        print(f"Intervalo de tempo: {self.data_inicio} a {self.data_fim}")
        print(f"Quantidade de funcionários: {len(self.FUNCIONARIOS)}")
        print(
            f"Quantidade de funcionários que precisam tirar férias: {len(self.FUNCIONARIOS_FERIAS)}"
        )
        print(
            f"Quantidade de funcionários que precisam fazer reciclagem: {len(self.FUNCIONARIOS_TREINAMENTO)}"
        )
        print("Vagas para reciclagem:")
        for i, n_vagas in self.p_vagas_treinamento.items():
            if n_vagas > 0:
                print(f"- {self.DIAS[i]}: {n_vagas}")
        print(
            pd.DataFrame(
                {
                    "Tempo de solução em segundos": [self.optimization_time],
                    "Gap de otimalidade": [round(self.optimization_gap, 6)],
                    "Solução": ["ótima" if self.optimization_status else "sub-ótima"],
                }
            ).to_string(index=False)
        )

        print()
        print("Solução:")
        print()
        print(f"Necessidade de contratação:")

        temp_df = pd.DataFrame(
            [
                [self.FUNCOES[p], max(self.v_alpha[i][p].x for i in self.DIAS)]
                for p in self.FUNCOES
            ],
            columns=["Função", "Necessidade de contratação"],
        )
        print(temp_df.to_string(index=False))
        print()
        print(
            f"Quantidade hora extra além do limite: {sum(self.v_hora_extra_extra[i][f].x for f in self.FUNCIONARIOS for i in self.DIAS)}"
        )
        print()
        print("Quantidade por escala:")
        temp_df = pd.DataFrame(
            [
                [self.ESCALAS[e], sum(self.v_escala[f][e].x for f in self.FUNCIONARIOS)]
                for e in self.ESCALAS
            ],
            columns=["Escala", "Quantidade de funcionários alocados"],
        )
        print(temp_df.to_string(index=False))

        print()
        print("Alocação de férias:")
        print(
            f"- total: {sum(self.v_inicio_ferias[i][f].x for i in self.DIAS for f in self.FUNCIONARIOS_FERIAS)}"
        )

        temp_df = pd.DataFrame(
            [
                [
                    self.FUNCIONARIOS_FERIAS[f],
                    self.DIAS[i],
                    self.DIAS[
                        min(i + self.p_duracao_ferias[f] - 1, len(self.DIAS) - 1)
                    ],
                ]
                for i in self.DIAS
                for f in self.FUNCIONARIOS_FERIAS
                if self.v_inicio_ferias[i][f].x >= 0.99
            ],
            columns=[
                "Funcionário",
                "Data de início das férias",
                "Data de término das férias",
            ],
        )
        print(temp_df.to_string(index=False))

        print()
        print("Alocação de reciclagem:")
        print(
            f"- total: {sum(self.v_treinamento[i][f].x for i in self.DIAS for f in self.FUNCIONARIOS_TREINAMENTO)}"
        )

        temp_df = pd.DataFrame(
            [
                [
                    self.FUNCIONARIOS_TREINAMENTO[f],
                    self.DIAS[i],
                ]
                for i in self.DIAS
                for f in self.FUNCIONARIOS_TREINAMENTO
                if self.v_treinamento[i][f].x >= 0.99
            ],
            columns=[
                "Funionário",
                "Data da reciclagem",
            ],
        )
        print(temp_df.to_string(index=False))

        print()
        print("Horas extras:")
        total_hora_extra = sum(
            self.p_duracao_jornada_horas[j] - self.p_escala_duracao_jornada_horas[i, e]
            for f in self.FUNCIONARIOS
            for i in self.DIAS
            for e in self.ESCALAS
            for j in self.JORNADAS
            if (
                i,
                self.FUNCAO_FUNCIONARIO[f],
                j,
            )
            in self.DIAS_FUNCOES_JORNADAS
            and self.v_hora_extra[i][f].x >= 0.99
            and self.p_duracao_jornada_horas[j]
            - self.p_escala_duracao_jornada_horas[i, e]
            > 0
        )
        print(f"Total = {round(total_hora_extra, 2)} horas")

        data = []
        for i in self.DIAS:
            total_horas_normais = sum(
                min(
                    self.p_duracao_jornada_horas[j],
                    self.p_escala_duracao_jornada_horas[i, e],
                )
                for f in self.FUNCIONARIOS
                for e in self.ESCALAS
                for j in self.JORNADAS
                if (
                    i,
                    self.FUNCAO_FUNCIONARIO[f],
                    j,
                )
                in self.DIAS_FUNCOES_JORNADAS
                and self.v_hora_extra[i][f].x >= 0.99
            )
            total_hora_extra_temp = sum(
                self.p_duracao_jornada_horas[j]
                - self.p_escala_duracao_jornada_horas[i, e]
                for f in self.FUNCIONARIOS
                for e in self.ESCALAS
                for j in self.JORNADAS
                if (
                    i,
                    self.FUNCAO_FUNCIONARIO[f],
                    j,
                )
                in self.DIAS_FUNCOES_JORNADAS
                and self.v_hora_extra[i][f].x >= 0.99
                and self.p_duracao_jornada_horas[j]
                - self.p_escala_duracao_jornada_horas[i, e]
                > 0
            )
            data.append(
                [
                    self.DIAS[i],
                    round(total_horas_normais, 2),
                    round(total_hora_extra_temp, 2),
                    round(
                        div_or_zero(total_hora_extra_temp, total_horas_normais) * 100, 2
                    ),
                ]
            )

        temp_df = pd.DataFrame(
            data,
            columns=[
                "Data",
                "Horas normais",
                "Hora extra utilizada",
                "Proporção extra/normal %",
            ],
        )
        print(temp_df.to_string(index=False))

    def get_dict_output_simulator(self):
        return {
            "disponibilidade_funcao": {
                self.DIAS[i]: {
                    self.FUNCOES[p]: sum(
                        self.v_trabalho[i][f][e][j].x
                        for f in [
                            index
                            for index, value in self.FUNCAO_FUNCIONARIO.items()
                            if value == p
                        ]
                        for e in self.ESCALAS
                        for j in self.JORNADAS
                        if (i, p, j) in self.DIAS_FUNCOES_JORNADAS
                    )
                    for p in self.FUNCOES
                }
                for i in self.DIAS
            }
        }

    def get_dict_output(self):

        return {
            "objective_value": self.model.objective_value,
            "opt_duration_seconds": self.optimization_time,
            "escalas": {
                self.ESCALAS[e]: [
                    self.FUNCIONARIOS[f]
                    for f in self.FUNCIONARIOS
                    if self.v_escala[f][e].x and self.v_escala[f][e].x >= 0.99
                ]
                for e in self.ESCALAS
            },
            "ferias": {
                self.FUNCIONARIOS[f]: self.DIAS[i]
                for i in self.DIAS
                for f in self.FUNCIONARIOS
                if self.v_inicio_ferias[i][f].x and self.v_inicio_ferias[i][f].x >= 0.99
            },
            "treinamento": {
                self.FUNCIONARIOS[f]: self.DIAS[i]
                for i in self.DIAS
                for f in self.FUNCIONARIOS
                if self.v_treinamento[i][f].x and self.v_treinamento[i][f].x >= 0.99
            },
            "contratacao": {
                self.FUNCOES[p]: max(self.v_alpha[i][p].x for i in self.DIAS)
                for p in self.FUNCOES
            },
            "disponibilidade_funcao": {
                self.DIAS[i]: {
                    self.FUNCOES[p]: sum(
                        self.v_trabalho[i][f][e][j].x
                        for f in [
                            index
                            for index, value in self.FUNCAO_FUNCIONARIO.items()
                            if value == p
                        ]
                        for e in self.ESCALAS
                        for j in self.JORNADAS
                        if (i, p, j) in self.DIAS_FUNCOES_JORNADAS
                    )
                    for p in self.FUNCOES
                }
                for i in self.DIAS
            },
            "disponibilidade_funcao_pessoa": {
                self.DIAS[i]: {
                    self.FUNCOES[p]: [
                        self.FUNCIONARIOS[f]
                        for f in [
                            index
                            for index, value in self.FUNCAO_FUNCIONARIO.items()
                            if value == p
                        ]
                        for e in self.ESCALAS
                        if sum(
                            self.v_trabalho[i][f][e][j].x
                            for j in self.JORNADAS
                            if (i, p, j) in self.DIAS_FUNCOES_JORNADAS
                        )
                        >= 0.99
                    ]
                    for p in self.FUNCOES
                }
                for i in self.DIAS
            },
        }

    def get_df_escala_funcionario(self):
        return pd.DataFrame(
            {
                "funcionário": [
                    self.FUNCIONARIOS[f]
                    for f in self.FUNCIONARIOS
                    for e in self.ESCALAS
                    if self.v_escala[f][e].x and self.v_escala[f][e].x >= 0.99
                ],
                "escala": [
                    self.ESCALAS[e]
                    for f in self.FUNCIONARIOS
                    for e in self.ESCALAS
                    if self.v_escala[f][e].x and self.v_escala[f][e].x >= 0.99
                ],
            }
        )

    def get_df_escala_prevista(self):
        df1 = pd.DataFrame(
            {
                "data": [i for i in self.DIAS.values() for _ in self.FUNCIONARIOS],
                "cód. filial": [
                    self.cod_filial
                    for _ in self.DIAS.values()
                    for _ in self.FUNCIONARIOS
                ],
                "funcionário": [
                    f for _ in self.DIAS.values() for f in self.FUNCIONARIOS.values()
                ],
                "alocação": [
                    (
                        "E"
                        if sum(
                            self.v_trabalho[i][f][e][j].x
                            for e in self.ESCALAS
                            for j in self.JORNADAS
                            if (i, self.FUNCAO_FUNCIONARIO[f], j)
                            in self.DIAS_FUNCOES_JORNADAS
                        )
                        >= 0.99
                        else (
                            "FE"
                            if (
                                self.v_inicio_ferias[i][f].x
                                + sum(
                                    self.v_inicio_ferias[_i][f].x
                                    for _i in range(
                                        i - 1,
                                        max(i - self.p_duracao_ferias[f], -1),
                                        -1,
                                    )
                                )
                                if f in self.FUNCIONARIOS_FERIAS
                                else 0
                            )
                            >= 0.99
                            else (
                                "R"
                                if (
                                    i in self.FUNCIONARIOS_TREINAMENTO
                                    and self.v_treinamento[i][f].x >= 0.99
                                )
                                else "F"
                            )
                        )
                    )
                    for i in self.DIAS
                    for f in self.FUNCIONARIOS
                ],
            }
        )

        return df1

    def get_df_demanda_nao_atendida(self):
        return pd.DataFrame(
            {
                "data": [i for i in self.DIAS.values() for p in self.FUNCOES],
                "cód. filial": [
                    self.cod_filial for _ in self.DIAS for _ in self.FUNCOES
                ],
                "função": [p for _ in self.DIAS for p in self.FUNCOES.values()],
                "quantidade de demanda não atendida": [
                    self.v_alpha[i][p].x for i in self.DIAS for p in self.FUNCOES
                ],
            }
        )

    def get_df_output(self):
        df = pd.DataFrame(
            {
                "dia": [i for i in self.DIAS.values() for _ in self.FUNCOES],
                "funcao": [self.FUNCOES[p] for _ in self.DIAS for p in self.FUNCOES],
                "demanda": [
                    self.p_demanda[i, p] for i in self.DIAS for p in self.FUNCOES
                ],
                "disponível": [
                    sum(
                        self.v_escala[f][e].x * self.p_dias_ativos_escala[i, e]
                        for f in [
                            index
                            for index, value in self.FUNCAO_FUNCIONARIO.items()
                            if value == p
                        ]
                        for e in self.ESCALAS
                    )
                    for i in self.DIAS
                    for p in self.FUNCOES
                ],
                "contratação": [
                    self.v_alpha[i][p].x for i in self.DIAS for p in self.FUNCOES
                ],
                "alocado": [
                    sum(
                        self.v_trabalho[i][f][e][j].x
                        for f in [
                            index
                            for index, value in self.FUNCAO_FUNCIONARIO.items()
                            if value == p
                        ]
                        for e in self.ESCALAS
                        for j in self.JORNADAS
                        if (i, p, j) in self.DIAS_FUNCOES_JORNADAS
                    )
                    for i in self.DIAS
                    for p in self.FUNCOES
                ],
                "ferias": [
                    sum(
                        (
                            self.v_inicio_ferias[i][f].x
                            + sum(
                                self.v_inicio_ferias[_i][f].x
                                for _i in range(
                                    i - 1, max(i - self.p_duracao_ferias[f], -1), -1
                                )
                            )
                            if f in self.FUNCIONARIOS_FERIAS
                            else 0
                        )
                        for f in [
                            index
                            for index, value in self.FUNCAO_FUNCIONARIO.items()
                            if value == p
                        ]
                    )
                    for i in self.DIAS
                    for p in self.FUNCOES
                ],
                "treinamento": [
                    sum(
                        self.v_treinamento[i][f].x
                        for f in [
                            index
                            for index, value in self.FUNCAO_FUNCIONARIO.items()
                            if value == p
                        ]
                    )
                    for i in self.DIAS
                    for p in self.FUNCOES
                ],
            }
        )
        df["ocisoso"] = (
            df["disponível"] - df["alocado"] - df["ferias"] - df["treinamento"]
        )
        df.loc[df["disponível"] == 0, "ocisoso"] = 0
        df.loc[df["contratação"] > 0, "ocisoso"] = 0
        return df


class OtimizadorFerias:

    def __init__(
        self,
        mes_inicio: int,
        ano_inicio: int,
        mes_fim: int,
        ano_fim: int,
        FUNCIONARIOS: Dict[int, str],
        FUNCOES: Dict[int, str],
        FUNCAO_FUNCIONARIO: Dict[int, str],
        PARTICOES: Dict[int, int],
        PARTICOES_FUNCIONARIOS: Dict[int, str],
        p_demanda: Dict[Tuple[int, int], int],
        p_mes_minimo: Dict[int, int],
        p_mes_maximo: Dict[int, int],
        p_beta: Dict[int, int],
    ):
        self.MESES = {
            i: data
            for i, data in enumerate(
                gerar_lista_meses(mes_inicio, ano_inicio, mes_fim, ano_fim)
            )
        }
        self.FUNCIONARIOS = FUNCIONARIOS
        self.FUNCOES = FUNCOES
        self.FUNCAO_FUNCIONARIO = FUNCAO_FUNCIONARIO
        self.PARTICOES = PARTICOES
        self.PARTICOES_FUNCIONARIOS = PARTICOES_FUNCIONARIOS
        self.p_demanda = p_demanda
        self.p_mes_minimo = p_mes_minimo
        self.p_mes_maximo = p_mes_maximo
        self.p_beta = p_beta

    def run(self):
        self.model = Model()

        # Variáveis
        self.v_alocacao = [
            [
                [self.model.add_var(var_type=BINARY) for r in self.PARTICOES]
                for f in self.FUNCIONARIOS
            ]
            for m in self.MESES
        ]
        self.v_quebra_total = [
            self.model.add_var(var_type=INTEGER) for p in self.FUNCOES
        ]
        self.v_quebra_mensal = [
            [self.model.add_var(var_type=INTEGER) for p in self.FUNCOES]
            for m in self.MESES
        ]

        self.model.objective = minimize(
            len(self.MESES) * xsum(self.v_quebra_total[p] for p in self.FUNCOES)
            + xsum(self.v_quebra_mensal[m][p] for p in self.FUNCOES for m in self.MESES)
        )

        for f in self.FUNCIONARIOS:
            for r in self.PARTICOES_FUNCIONARIOS[f]:
                self.model += xsum(self.v_alocacao[m][f][r] for m in self.MESES) == 1

        # for f in self.FUNCIONARIOS:
        #     if len(self.PARTICOES_FUNCIONARIOS[f]) > 1:
        #         for m_ in self.MESES:
        #             for j, r in enumerate(self.PARTICOES_FUNCIONARIOS[f][1:]):
        #                 self.model += self.v_alocacao[m_][f][r] <= xsum(
        #                     self.v_alocacao[m][f][self.PARTICOES_FUNCIONARIOS[f][j - 1]]
        #                     for m in self.MESES
        #                     if m < m_
        #                 )
        for m in self.MESES:
            for f in self.FUNCIONARIOS:
                if m < self.p_mes_minimo[f] or m > self.p_mes_maximo[f]:
                    for r in self.PARTICOES_FUNCIONARIOS[f]:
                        self.model += self.v_alocacao[m][f][r] == 0

        for m in self.MESES:
            for p in self.FUNCOES:
                self.model += self.v_quebra_mensal[m][p] >= self.p_demanda[m, p] - (
                    self.p_beta[p]
                    - xsum(
                        self.v_alocacao[m][f][r]
                        for f in [
                            index
                            for index, value in self.FUNCAO_FUNCIONARIO.items()
                            if value == p
                        ]
                        for r in self.PARTICOES_FUNCIONARIOS[f]
                    )
                )

        for m in self.MESES:
            for p in self.FUNCOES:
                self.model += self.v_quebra_total[p] >= self.v_quebra_mensal[m][p]
        ref = time()
        self.model.optimize()
        self.optimization_time = round(time() - ref, 2)

    def get_dict_output(self):

        return {
            "objective_value": self.model.objective_value,
            "opt_duration_seconds": self.optimization_time,
            "ferias": {
                self.FUNCIONARIOS[f]: {
                    self.MESES[m]: self.PARTICOES[r]
                    for m in self.MESES
                    for r in self.PARTICOES_FUNCIONARIOS[f]
                    if self.v_alocacao[m][f][r].x and self.v_alocacao[m][f][r].x >= 0.99
                }
                for f in self.FUNCIONARIOS
            },
        }

    def get_df_output(self):
        return pd.DataFrame(
            {
                "mês": [
                    self.MESES[m]
                    for m in self.MESES
                    for f in self.FUNCIONARIOS
                    for r in self.PARTICOES_FUNCIONARIOS[f]
                ],
                "funcionário": [
                    self.FUNCIONARIOS[f]
                    for m in self.MESES
                    for f in self.FUNCIONARIOS
                    for r in self.PARTICOES_FUNCIONARIOS[f]
                ],
                "função": [
                    self.FUNCOES[self.FUNCAO_FUNCIONARIO[f]]
                    for m in self.MESES
                    for f in self.FUNCIONARIOS
                    for r in self.PARTICOES_FUNCIONARIOS[f]
                ],
                "ferias": [
                    self.PARTICOES[r] if self.v_alocacao[m][f][r].x >= 0.99 else 0
                    for m in self.MESES
                    for f in self.FUNCIONARIOS
                    for r in self.PARTICOES_FUNCIONARIOS[f]
                ],
            }
        ), pd.DataFrame(
            {
                "mês": [self.MESES[m] for m in self.MESES for p in self.FUNCOES],
                "função": [self.FUNCOES[p] for m in self.MESES for p in self.FUNCOES],
                "demana": [
                    self.p_demanda[m, p] for m in self.MESES for p in self.FUNCOES
                ],
                "capacidade": [
                    self.p_beta[p] for m in self.MESES for p in self.FUNCOES
                ],
            }
        )


if __name__ == "__main__":
    # otimizador = OtimizadorEscalas(
    #     5,
    #     2024,
    #     {0: "t"},
    #     {0: "t"},
    #     {0: "t"},
    #     {0: "t"},
    #     {0: "t"},
    #     {0: "t"},
    #     {(0, 0): 0},
    #     {(0, 0): 0},
    #     {(0, 0): 0},
    #     {0: 0},
    #     {0: 0},
    # )
    opt = OtimizadorFerias(
        1, 2023, 6, 2024, {0: "t"}, {0: "t"}, {0: "t"}, {0: 0}, {(0, 0): 0}
    )
