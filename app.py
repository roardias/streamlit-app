import streamlit as st
from datetime import datetime

# Define as funções do seu código original
def calcular_datas_vencimento(data_solicitacao, parcelas):
    data_solicitacao = datetime.strptime(data_solicitacao, '%d/%m/%Y')
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
    if escolha == '1':
        TC = 150.29
        Seguro = 77.70
        valor_financiado = float(valor) + TC + Seguro
    elif escolha == '2':
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

def main():
    st.title('Calculadora de Empréstimo/Antecipação Salarial')

    escolha = st.radio("Você quer empréstimo ou antecipação salarial?", ('Empréstimo', 'Antecipação Salarial'))
    valor = st.number_input("Qual valor deseja? (em reais)", min_value=0.0, step=0.01)
    taxa_juros = st.number_input("Qual a taxa de juros mensal? (%)", min_value=0.0, step=0.01)
    data_solicitacao = st.date_input("Qual a data de solicitação?")

    if escolha == 'Empréstimo':
        parcelas = st.slider("Em quantas parcelas deseja parcelar? (máximo de 60 vezes)", min_value=1, max_value=60)
