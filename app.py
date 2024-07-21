import streamlit as st
from datetime import datetime
import pandas as pd
import pytz

tz = pytz.timezone('America/Sao_Paulo')

def calcular_datas_vencimento(data_solicitacao, parcelas):
    data_solicitacao = datetime.now(tz).strptime(data_solicitacao, '%d/%m/%Y')
    if data_solicitacao.day <= 10:
        if data_solicitacao.month == 12:
            primeira_parcela = data_solicitacao.replace(day=10, month=1, year=data_solicitacao.year + 1)
        else:
            primeira_parcela = data_solicitacao.replace(day=10, month=data_solicitacao.month + 1)
    else:
        if data_solicitacao.month == 12:
            primeira_parcela = data_solicitacao.replace(day=10, month=2, year=data_solicitacao.year + 1)
        else:
            primeira_parcela = data_solicitacao.replace(day=10, month=data_solicitacao.month + 2)
    datas_vencimento = [primeira_parcela]
    for i in range(1, parcelas):
        mes = (primeira_parcela.month + i - 1) % 12 + 1
        ano = primeira_parcela.year + (primeira_parcela.month + i - 1) // 12
        datas_vencimento.append(datetime(year=ano, month=mes, day=10))
    return datas_vencimento

def calcular_dias_vencimento(datas_vencimento, data_solicitacao):
    dias_vencimento = []
    dias_acumulados = []
    for i, data_venc in enumerate(datas_vencimento):
        if i == 0:
            dias = (data_venc - data_solicitacao).days
        else:
            dias = (data_venc - datas_vencimento[i - 1]).days
        dias_vencimento.append(dias)
        if i == 0:
            dias_acumulados.append(dias)
        else:
            dias_acumulados.append(dias_acumulados[i - 1] + dias)
    return dias_vencimento, dias_acumulados

def calcular_fatores(taxa_juros, dias_acumulados):
    fatores = []
    taxa_juros_decimal = float(taxa_juros) / 100
    for dias in dias_acumulados:
        fator = 1 / ((1 + taxa_juros_decimal) ** (dias / 30))
        fatores.append(fator)
    return fatores

def calcular_coeficiente(fatores):
    soma_fatores = sum(fatores)
    coeficiente = 1 / soma_fatores
    return coeficiente

def calcular_valor_financiado(valor, escolha):
    if escolha == 'Empréstimo':
        TC = 150.29
        Seguro = 77.70
        valor_financiado = float(valor) + TC + Seguro
    elif escolha == 'Antecipação Salarial':
        TC_Antecipacao = 50.00
        valor_financiado = float(valor) + TC_Antecipacao
    return valor_financiado

def calcular_taxa_juros_parcela(taxa_juros, dias_vencimento):
    taxas_juros = []
    taxa_juros_decimal = float(taxa_juros) / 100
    for dias in dias_vencimento:
        taxa_parcela = ((1 + taxa_juros_decimal) ** (dias / 30)) - 1
        taxas_juros.append(taxa_parcela * 100)
    return taxas_juros

def calcular_valor_prestacao(valor_financiado, coeficiente):
    return valor_financiado * coeficiente

def calcular_iof_diario(amortizacoes, dias_acumulados):
    iof_diario = []
    for amortizacao, dias in zip(amortizacoes, dias_acumulados):
        if dias > 365:
            iof_parcela = amortizacao * 0.03
        else:
            iof_parcela = amortizacao * dias * 0.000082
        iof_diario.append(iof_parcela)
    return iof_diario

def calcular_iof_adicional(valor_financiado):
    return valor_financiado * 0.0038

def calcular_amortizacao_e_saldo_devedor(valor_financiado, coeficiente, parcelas, taxas_juros_parcela, dias_acumulados):
    saldo_devedor = valor_financiado
    amortizacoes = []
    saldos_devedores = []
    iof_diario_parcelas = []

    for i in range(parcelas):
        juros_parcela = saldo_devedor * (taxas_juros_parcela[i] / 100)
        saldo_devedor += juros_parcela
        amortizacao = calcular_valor_prestacao(valor_financiado, coeficiente) - juros_parcela
        saldo_devedor_final = saldo_devedor - calcular_valor_prestacao(valor_financiado, coeficiente)

        if dias_acumulados[i] > 365:
            iof_diario = amortizacao * 0.03
        else:
            iof_diario = amortizacao * dias_acumulados[i] * 0.000082
        iof_diario_parcelas.append(iof_diario)

        amortizacoes.append(amortizacao)
        saldos_devedores.append(saldo_devedor_final)
        saldo_devedor = saldo_devedor_final

    return amortizacoes, saldos_devedores, iof_diario_parcelas

def set_css():
    st.markdown(
        """
        <style>
        .stApp {
            background-color: #f7f5ff;
            padding: 20px;
            border-radius: 10px;
        }
        .stTextInput > div > input,
        .stNumberInput > div > div > input {
            background-color: #ffffff;
            border: 1px solid #d1d1d1;
            border-radius: 5px;
            padding: 10px;
            width: 100%;
            margin-bottom: 10px;
            font-size: 16px;
        }
        .stRadio > div {
            display: flex;
            flex-direction: row;
            background-color: #ffffff;
            border-radius: 5px;
            padding: 10px;
            border: 1px solid #d1d1d1;
            margin-top: 10px;
        }
        .stRadio > div > label {
            color: #333333;
            font-weight: bold;
            margin-right: 20px;
        }
        .stRadio > div > div > label {
            color: #333333;
        }
        .stRadio > div > div > label:hover {
            color: #007acc;
        }
        .stButton > button {
            background-color: #6200ee;
            color: white;
            border: none;
            border-radius: 5px;
            padding: 10px 20px;
            font-size: 16px;
            cursor: pointer;
        }
        .stButton > button:hover {
            background-color: #4500cb;
        }
        .stDataFrame table {
            border-collapse: collapse;
            width: 100%;
            margin: auto;
            border-radius: 5px;
            overflow: hidden;
            table-layout: fixed;
        }
        .stDataFrame table th,
        .stDataFrame table td {
            border: 1px solid #d1d1d1;
            text-align: center;
            padding: 10px;
            font-size: 14px;
        }
        .stDataFrame table thead th {
            background-color: #6200ee;
            color: white;
        }
        .stDataFrame table tbody tr:nth-child(even) {
            background-color: #f2f2f2;
        }
        .stDataFrame table tbody tr:hover {
            background-color: #e0e0e0;
        }
        .stMarkdown h1 {
            color: #333333;
        }
        .stMarkdown p {
            color: #333333;
        }
        .stRadio > div > label,
        .stNumberInput > label,
        .stTextInput > label {
            color: #333333;
        }
        .stRadio > div > div > label {
            text-align: center;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

def main():
    st.set_page_config(page_title="Simulador de Empréstimo", layout="wide")
    set_css()

    st.markdown('<h1 style="color: #333333;">Simulador de Empréstimo</h1>', unsafe_allow_html=True)

    if "reset_form" not in st.session_state:
        st.session_state.reset_form = False

    if st.session_state.reset_form:
        st.session_state.valor = 0.0
        st.session_state.taxa_juros = 0.0
        st.session_state.parcelas = 1
        st.session_state.escolha = "Pessoal"
        st.session_state.reset_form = False

    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        st.markdown('<p style="color: #333333; font-weight: bold;">Qual o tipo de empréstimo desejado?</p>', unsafe_allow_html=True)
        escolha = st.radio("", ('Pessoal', 'FGTS', 'Consignado', 'Com Garantia'), key='escolha')
    
    with col2:
        valor = st.number_input("Valor do empréstimo (R$):", min_value=0.0, step=0.01, key='valor')

    with col3:
        taxa_juros = st.number_input("Taxa de juros (%):", min_value=0.0, step=0.01, key='taxa_juros')

    parcelas = st.number_input("Número de parcelas:", min_value=1, step=1, key='parcelas')

    if st.button('CALCULAR'):
        try:
            data_solicitacao = datetime.now(tz).strftime('%d/%m/%Y')
            data_solicitacao_dt = datetime.strptime(data_solicitacao, '%d/%m/%Y')
            datas_vencimento = calcular_datas_vencimento(data_solicitacao, parcelas)
            dias_vencimento, dias_acumulados = calcular_dias_vencimento(datas_vencimento, data_solicitacao_dt)
            fatores = calcular_fatores(taxa_juros, dias_acumulados)
            coeficiente = calcular_coeficiente(fatores)
            taxas_juros_parcela = calcular_taxa_juros_parcela(taxa_juros, dias_vencimento)
            valor_financiado_inicial = calcular_valor_financiado(valor, escolha)
            valor_prestacao = calcular_valor_prestacao(valor_financiado_inicial, coeficiente)
            amortizacoes, saldos_devedores, iof_diario_parcelas = calcular_amortizacao_e_saldo_devedor(
                valor_financiado_inicial, coeficiente, parcelas, taxas_juros_parcela, dias_acumulados)
            iof_adicional = calcular_iof_adicional(valor_financiado_inicial)
            total_iof = iof_adicional + sum(iof_diario_parcelas)
            valor_financiado_com_iof = valor_financiado_inicial + total_iof
            valor_prestacao_com_iof = calcular_valor_prestacao(valor_financiado_com_iof, coeficiente)

            # Exibir resultados gerais
            st.markdown(f'<p style="color: #333333;">Valor solicitado: R$ {valor:,.2f}</p>', unsafe_allow_html=True)
            st.markdown(f'<p style="color: #333333;">Taxa de Juros: {taxa_juros}%</p>', unsafe_allow_html=True)
            st.markdown(f'<p style="color: #333333;">Quantidade de parcelas: {parcelas}</p>', unsafe_allow_html=True)

            data = {
               "Número da Parcela": list(range(1, parcelas + 1)),
               "Data de Vencimento": [data_venc.strftime('%d/%m/%Y') for data_venc in datas_vencimento],
               "Valor da Parcela": [f"R$ {valor_prestacao_com_iof:,.2f}" for _ in range(parcelas)]
            }
            df = pd.DataFrame(data)
            
            # Estilizar o DataFrame
            styled_df = df.style.set_table_styles(
                [{'selector': 'table',
                    'props': [('border', '1px solid black')]},
                 {'selector': 'td',
                    'props': [('border', '1px solid black'), ('white-space', 'nowrap')]},
                 {'selector': 'th',
                    'props': [('border', '1px solid black'), ('white-space', 'nowrap')]}]
            ).set_properties(**{'text-align': 'center'}).hide(axis='index')

            # Exibir o DataFrame no Streamlit
            st.dataframe(styled_df, use_container_width=True, hide_index=True)

            # Reset the form fields
            st.session_state.reset_form = True

        except ValueError as e:
            st.error(f"Ocorreu um erro ao processar os dados: {e}")
        except Exception as e:
            st.error(f"Ocorreu um erro inesperado: {e}")

if __name__ == "__main__":
    main()
