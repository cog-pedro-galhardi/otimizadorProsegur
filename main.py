from copy import copy
from optimizer import (
    dias_uteis_5_por_2,
    dias_uteis_6_por_1,
    dias_uteis_12_36_par,
    dias_uteis_12_36_impar,
    gerar_lista_datas,
    jornada_6_por_1_sab_4,
    jornada_6_por_1,
    jornada_5_por_2,
    jornada_12_36_par,
    jornada_12_36_impar,
    OtimizadorEscalas,
)
import pandas as pd
import streamlit as st
import base64
import uuid
import re

st.set_page_config(page_title="Modelo de otimização", page_icon="assets/cog.png")
st.markdown(
    """
    <style>

    div.stButton > button {
        background-color: #007BFF;
        color: white;
        border-radius: 5px;
        padding: 10px 20px;
        border: none;
    }

    div.stButton > button:hover {
        background-color: #0056b3;
        color: white;
    }

    div.stDownloadButton > button {
        background-color: #007BFF;
        color: white;
        border-radius: 5px;
        padding: 10px 20px;
        border: none;
        font-size: 16px;
    }

    div.stDownloadButton > button:hover {
        background-color: #0056b3;
        color: white;
    }

    </style>
    """,
    unsafe_allow_html=True,
)
st.markdown(
    "<h1 style='color: #007BFF;'>Modelo de otimização</h1>", unsafe_allow_html=True
)


# salvando os arquivos em cache
@st.cache_data
def carregar_arquivo(file):
    return pd.read_csv(file)


# sidebar para o menu de navegação
st.sidebar.title("Menu de Navegação")
menu_option = st.sidebar.radio(
    "Navegue para:",
    [
        "Previsão de Demanda",
        "Modelo de Otimização",
        "Modelo de Simulação",
    ],
)

if menu_option == "Previsão de Demanda":
    st.sidebar.write("Redirecionando para Previsão de Demanda ")
    st.sidebar.markdown(
        "[Clique aqui](https://prossegurprevisao-cognitivo.streamlit.app/)",
        unsafe_allow_html=True,
    )

elif menu_option == "Modelo de Otimização":
    st.sidebar.write("Redirecionando para Modelo de Otimização")
    st.sidebar.markdown(
        "[Clique aqui](https://sua-aplicacao-aws-2.com)", unsafe_allow_html=True
    )

elif menu_option == "Modelo de Simulação":
    st.sidebar.write("Redirecionando para Modelo de Simulação")
    st.sidebar.markdown(
        "[Clique aqui](https://sua-aplicacao-streamlit-cloud.com)",
        unsafe_allow_html=True,
    )


st.markdown(
    "<h5 style='color: #007BFF;'>Selecione o arquivo gerado pela previsão de demanda 'previsoes_resultado.csv'.</h5>",
    unsafe_allow_html=True,
)
demand = st.file_uploader(
    "Selecione o arquivo de previsão de resultados:",
    type="csv",
    key="file_uploader_demand",
    label_visibility="collapsed",
)

st.markdown(
    "<h5 style='color: #007BFF;'>Selecione o arquivo de equipes no formato CSV.</h5>",
    unsafe_allow_html=True,
)
equipes = st.file_uploader(
    "Selecione o arquivo de equipes:",
    type="csv",
    key="file_uploader_equipes",
    label_visibility="collapsed",
)

st.markdown(
    "<h5 style='color: #007BFF;'>Selecione o arquivo de regras CCT no formato CSV.</h5>",
    unsafe_allow_html=True,
)
regras = st.file_uploader(
    "Selecione o arquivo de regras CCT:",
    type="csv",
    key="file_uploader_regras",
    label_visibility="collapsed",
)

st.markdown(
    "<h5 style='color: #007BFF;'>Por favor, selecione a filial desejada.</h5>",
    unsafe_allow_html=True,
)
codigo_filial = st.selectbox(
    "Selecione a filial:",
    ["6", "116", "170", "75"],
    placeholder="Selecione uma filial.",
    label_visibility="collapsed",
)


if st.button("Processar Dados"):

    if demand is not None and equipes is not None and regras is not None:

        st.success("Arquivos carregados com sucesso! Iniciando processamento.")

        def main():
            progress = st.progress(0)
            total_etapas = 4
            progress_contador = 0
            progress_contador += 1
            progress.progress(progress_contador / total_etapas)

            df_demand = carregar_arquivo(demand)
            df_equipes = carregar_arquivo(equipes)
            df_regras_cct = carregar_arquivo(regras)

            df_demand["JORNADA"] = df_demand["JORNADA"].replace(
                {
                    "till 13": "more than 12",
                    "till 14": "more than 12",
                    "greater than 14": "more than 12",
                }
            )
            df_demand = (
                df_demand.groupby(
                    ["DATA COMPETÊNCIA", "CODIGO FILIAL", "TIPO VEÍCULO", "JORNADA"]
                )["QNT_ROTAS"]
                .sum()
                .reset_index()
            )
            cod_filial_list = [int(codigo_filial)]
            tempo = {6: 480, 116: 480, 170: 120, 75: 120}

            for cod_filial in cod_filial_list:
                st.write(f"Processando filial {cod_filial}")
                print(f"calculando filial {cod_filial} ...")
                FUNCIONARIOS = (
                    df_equipes.loc[df_equipes["CODIGO FILIAL"] == cod_filial, "NOME"]
                    .reset_index(drop=True)
                    .to_dict()
                )
                FUNCIONARIOS_FERIAS = {}
                FUNCIONARIOS_TREINAMENTO = {}
                JORNADAS = {
                    0: "till 8",
                    1: "till 9",
                    2: "till 10",
                    3: "till 11",
                    4: "till 12",
                    5: "more than 12",
                }

                p_duracao_jornada_horas = {
                    0: 8,
                    1: 9,
                    2: 10,
                    3: 11,
                    4: 12,
                    5: 13,
                }

                FUNCOES = {
                    0: "VIGILANTE CARRO FORTE",
                    1: "CHEFE DE EQUIPE",
                    2: "MOTORISTA CARRO FORTE",
                    3: "DUMMY",
                }
                FUNCAO_FUNCIONARIO = {
                    f: {value: key for key, value in FUNCOES.items()}.get(
                        df_equipes.loc[
                            (df_equipes["CODIGO FILIAL"] == cod_filial)
                            & (df_equipes["NOME"] == nome),
                            "DESCRICAO_UNIORG",
                        ].values[0]
                    )
                    for f, nome in FUNCIONARIOS.items()
                }

                df_demand_temp = df_demand.loc[
                    df_demand["CODIGO FILIAL"] == cod_filial
                ].copy()
                data_inicio = df_demand_temp["DATA COMPETÊNCIA"].min()
                data_fim = df_demand_temp["DATA COMPETÊNCIA"].max()
                num_dias = len(gerar_lista_datas(data_inicio, data_fim))

                df_cct = df_regras_cct.loc[
                    df_regras_cct["Estado"]
                    == df_equipes.loc[
                        df_equipes["CODIGO FILIAL"] == cod_filial, "UF"
                    ].unique()[0]
                ]

                cct_dict = (
                    df_cct.set_index("Estado")
                    .stack()
                    .reset_index()
                    .set_index("level_1")[0]
                    .to_dict()
                )

                lista_escalas = ["5X2", "6X1", "12X36 Folga PAR", "12X36 Folga IMPAR"]
                lista_escalas_filtrada = copy(lista_escalas)

                p_escala_duracao_jornada_horas = {}
                p_escala_duracao_hora_extra = {}

                if cct_dict.get("5x2") == "Não":
                    lista_escalas_filtrada.remove("5X2")
                else:
                    p_escala_duracao_hora_extra.setdefault(0, 2)
                    for i, value in enumerate(
                        jornada_5_por_2(data_inicio=data_inicio, data_fim=data_fim)
                    ):
                        p_escala_duracao_jornada_horas.setdefault((i, 0), value)
                if cct_dict.get("6x1") == "Não":
                    lista_escalas_filtrada.remove("6X1")
                else:
                    p_escala_duracao_hora_extra.setdefault(1, 2)
                    for i, value in enumerate(
                        jornada_6_por_1(data_inicio=data_inicio, data_fim=data_fim)
                    ):
                        p_escala_duracao_jornada_horas.setdefault((i, 1), value)
                if cct_dict.get("12x36") == "Não":
                    lista_escalas_filtrada.remove("12X36 Folga PAR")
                    lista_escalas_filtrada.remove("12X36 Folga IMPAR")
                else:
                    p_escala_duracao_hora_extra.setdefault(2, 0)
                    p_escala_duracao_hora_extra.setdefault(3, 0)
                    for i, value in enumerate(
                        jornada_12_36_impar(data_inicio=data_inicio, data_fim=data_fim)
                    ):
                        p_escala_duracao_jornada_horas.setdefault((i, 2), value)
                    for i, value in enumerate(
                        jornada_12_36_par(data_inicio=data_inicio, data_fim=data_fim)
                    ):
                        p_escala_duracao_jornada_horas.setdefault((i, 3), value)
                ESCALAS = {i: value for i, value in enumerate(lista_escalas_filtrada)}

                p_escala_duracao_hora_extra = {0: 2, 1: 2, 2: 0, 3: 0}
                funcoes_escala = {
                    "5X2": dias_uteis_5_por_2,
                    "6X1": dias_uteis_6_por_1,
                    "12X36 Folga PAR": dias_uteis_12_36_impar,
                    "12X36 Folga IMPAR": dias_uteis_12_36_par,
                }
                p_dias_ativos_escala = {}

                for e in ESCALAS:
                    for i, value in enumerate(
                        funcoes_escala[ESCALAS[e]](data_inicio, data_fim)
                    ):
                        p_dias_ativos_escala.setdefault((i, e), value)
                df_formacao = pd.DataFrame(
                    {
                        "TIPO VEÍCULO": ["FORTE", "FORTE", "FORTE", "FORTE", "LEVE"],
                        "FUNCAO": [
                            "VIGILANTE CARRO FORTE",
                            "VIGILANTE CARRO FORTE",
                            "CHEFE DE EQUIPE",
                            "MOTORISTA CARRO FORTE",
                            "DUMMY",
                        ],
                    }
                )
                df_calculo_demanda = pd.merge(
                    df_demand_temp, df_formacao, on="TIPO VEÍCULO"
                )

                df_calculo_demanda = (
                    df_calculo_demanda.groupby(
                        ["DATA COMPETÊNCIA", "JORNADA", "FUNCAO"]
                    )[["QNT_ROTAS"]]
                    .sum()
                    .reset_index()
                    .sort_values(["DATA COMPETÊNCIA", "JORNADA", "FUNCAO"])
                )

                df_calculo_demanda["JORNADA"] = df_calculo_demanda["JORNADA"].map(
                    {value: key for key, value in JORNADAS.items()}
                )

                df_calculo_demanda["FUNCAO"] = df_calculo_demanda["FUNCAO"].map(
                    {value: key for key, value in FUNCOES.items()}
                )

                dias_dict = {
                    dia: i
                    for i, dia in enumerate(
                        df_calculo_demanda["DATA COMPETÊNCIA"].unique().tolist()
                    )
                }
                df_calculo_demanda["DATA COMPETÊNCIA"] = df_calculo_demanda[
                    "DATA COMPETÊNCIA"
                ].map(dias_dict)
                p_demanda = df_calculo_demanda.set_index(
                    ["DATA COMPETÊNCIA", "FUNCAO", "JORNADA"]
                )["QNT_ROTAS"].to_dict()
                DIAS_FUNCOES_JORNADAS = [key for key in p_demanda]

                p_dias_ativos_funcionario = {}
                for i in range(num_dias):
                    for f in FUNCIONARIOS:
                        p_dias_ativos_funcionario.setdefault((i, f), 1)

                p_vagas_treinamento = {i: 0 for i in range(num_dias)}
                p_duracao_ferias = {}

                otimizador = OtimizadorEscalas(
                    data_inicio,
                    data_fim,
                    FUNCIONARIOS=FUNCIONARIOS,
                    FUNCIONARIOS_FERIAS=FUNCIONARIOS_FERIAS,
                    FUNCIONARIOS_TREINAMENTO=FUNCIONARIOS_TREINAMENTO,
                    FUNCOES=FUNCOES,
                    FUNCAO_FUNCIONARIO=FUNCAO_FUNCIONARIO,
                    ESCALAS=ESCALAS,
                    JORNADAS=JORNADAS,
                    DIAS_FUNCOES_JORNADAS=DIAS_FUNCOES_JORNADAS,
                    p_demanda=p_demanda,
                    p_dias_ativos_funcionario=p_dias_ativos_funcionario,
                    p_vagas_treinamento=p_vagas_treinamento,
                    p_duracao_ferias=p_duracao_ferias,
                    p_escala_duracao_jornada_horas=p_escala_duracao_jornada_horas,
                    p_duracao_jornada_horas=p_duracao_jornada_horas,
                    p_escala_duracao_hora_extra=p_escala_duracao_hora_extra,
                    cod_filial=cod_filial,
                )

                progress_contador += 1
                progress.progress(progress_contador / total_etapas)

                otimizador.run(
                    priorizar_ferias=True,
                    max_seconds=tempo.get(cod_filial, 120),
                    max_mip_gap=0.01,
                    priorizar_hora_extra=False,  # Se True, o modelo vai preferir contratar mais para evitar hora extra, alocando pessoas em escalas de maior jornada
                )

                progress_contador += 1
                progress.progress(progress_contador / total_etapas)

                df_alocacao = otimizador.get_df_escala_prevista()
                df_escalas = otimizador.get_df_escala_funcionario()
                df_alocacao.to_csv(
                    f"data/filial_{cod_filial}_alocacao.csv", index=False
                )
                df_escalas.to_csv(f"data/filial_{cod_filial}_escala.csv", index=False)

                # mostrando as 5 primeiras linhas dos outputs
                st.write("Primeiras 5 linhas das alocações:")
                st.write(df_alocacao.head())
                st.write("Primeiras 5 linhas das escalas:")
                st.write(df_escalas.head())

                progress_contador += 1
                progress.progress(progress_contador / total_etapas)

                st.success("Processamento concluído!")

                def download_button_csv(file_path, download_filename, button_text):
                    try:
                        with open(file_path, "rb") as file:
                            data = file.read()
                        b64 = base64.b64encode(data).decode()
                        button_uuid = str(uuid.uuid4()).replace("-", "")
                        button_id = re.sub("\d+", "", button_uuid)

                        # estiliza o botão de download
                        custom_css = f"""
                        <style>
                            #{button_id} {{
                                background-color: #007BFF;
                                color: white;
                                padding: 0.5em 0.8em;
                                text-decoration: none;
                                border-radius: 4px;
                                border: 1px solid #007BFF;
                                display: inline-block;
                            }}
                            #{button_id}:hover {{
                                background-color: #0056b3;
                                color: white;
                                border-color: #0056b3;
                            }}
                            #{button_id}:active {{
                                background-color: #002299;
                                color: white;
                                border-color: #002299;
                            }}
                        </style>
                        """
                        # link de download
                        dl_link = (
                            custom_css
                            + f'<a download="{download_filename}" id="{button_id}" href="data:text/csv;base64,{b64}">{button_text}</a><br><br>'
                        )

                        return dl_link
                    except FileNotFoundError:
                        st.error(
                            f"Arquivo {file_path} não encontrado. Verifique se o processamento foi concluído corretamente."
                        )
                        return ""

                # botao para a alocacao .CSV
                st.subheader("Download dos Resultados")
                download_link_alocacao = download_button_csv(
                    f"data/filial_{cod_filial}_alocacao.csv",
                    f"filial_{cod_filial}_alocacao.csv",
                    "Baixar CSV de Alocação",
                )
                st.markdown(download_link_alocacao, unsafe_allow_html=True)

                # botao para a escala .CSV
                download_link_escalas = download_button_csv(
                    f"data/filial_{cod_filial}_escala.csv",
                    f"filial_{cod_filial}_escala.csv",
                    "Baixar CSV de Escalas",
                )
                st.markdown(download_link_escalas, unsafe_allow_html=True)

        if __name__ == "__main__":
            main()

    else:
        st.error("Por favor, carregue os arquivos CSV necessários.")
