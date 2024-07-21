import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
import streamlit.components.v1 as components

tz = pytz.timezone('America/Sao_Paulo')

def carregar_dados_cpf(cpf):
    try:
        df = pd.read_excel("Planilha/margens.xlsx", dtype=str, engine='openpyxl')
        return df[df["cpf2"] == cpf]
    except pd.errors.ParserError:
        st.error("Erro ao ler o arquivo Excel. Verifique o formato do arquivo.")
        return pd.DataFrame()
    except FileNotFoundError:
        st.error("Arquivo Excel não encontrado. Verifique o caminho do arquivo.")
        return pd.DataFrame()
    except ImportError:
        st.error("Biblioteca openpyxl não instalada. Execute 'pip install openpyxl' para instalá-la.")
        return pd.DataFrame()

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

def carregar_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

def set_numeric_input_js():
    components.html(
        """
        <script>
        const elements = document.querySelectorAll('input[type="number"]');
        elements.forEach(element => {
            element.setAttribute('inputmode', 'numeric');
        });
        </script>
        """,
        height=0,
    )

def main():
    st.set_page_config(page_title="Calculadora de Empréstimo/Antecipação Salarial", layout="wide")
    carregar_css("style.css")
    set_numeric_input_js()

    st.image("images/MARCA_CONSIGO_CRED_VETOR_CURVAS_5.png", width=200)
    st.markdown('<h1 style="color: #7CB26E;">Calculadora de Empréstimo/Antecipação Salarial</h1>', unsafe_allow_html=True)

    if "cpf_validado" not in st.session_state:
        st.session_state.cpf_validado = False

    if not st.session_state.cpf_validado:
        cpf = st.text_input("Digite seu CPF (somente números):", max_chars=11)
        if len(cpf) == 11 and cpf.isdigit():
            if st.button('Buscar'):
                dados_cpf = carregar_dados_cpf(cpf)
                if not dados_cpf.empty:
                    st.session_state.cpf_validado = True
                    st.session_state.dados_cpf = dados_cpf.to_dict(orient='records')[0]
                else:
                    st.warning("Infelizmente não localizamos seu CPF em nossa base de cadastro, confira se digitou corretamente ou entre em contato com RH da sua empresa.")
        else:
            st.warning("Por favor, insira um CPF válido com 11 dígitos.")
    else:
        dados_cpf = st.session_state.dados_cpf
        nome = dados_cpf["Nome"]
        empresa = dados_cpf["Empresa"]
        margem = float(dados_cpf["Margem"])
        parcela_maxima = float(dados_cpf["Parcela Maxima"])

        st.markdown(f"<p>Olá {nome}, confira as informações abaixo:</p>", unsafe_allow_html=True)
        st.markdown(f"<p>Trabalha na empresa: {empresa}</p>", unsafe_allow_html=True)
        st.markdown(f"<p>Margem pré-aprovada: R$ {margem:,.2f}</p>", unsafe_allow_html=True)
        st.markdown(f"<p>Parcela máxima: R$ {parcela_maxima:,.2f}</p>", unsafe_allow_html=True)

        if "reset_form" not in st.session_state:
            st.session_state.reset_form = False

        if st.session_state.reset_form:
            st.session_state.valor = 0.0
            st.session_state.taxa_juros = 0.0
            st.session_state.parcelas = 1
            st.session_state.escolha = "Empréstimo"
            st.session_state.reset_form = False

        col1, col2 = st.columns([1, 2])

        with col1:
            st.markdown('<p style="color: #7CB26E; font-weight: bold;">Tipo de operação:</p>', unsafe_allow_html=True)
            escolha = st.radio("", ('Empréstimo', 'Antecipação Salarial'), key='escolha')

            st.markdown(f'<p style="color: #7CB26E;">Data de solicitação: {datetime.now(tz).strftime("%d/%m/%Y")}</p>', unsafe_allow_html=True)
            if escolha == 'Empréstimo':
                valor = st.number_input("Valor solicitado (R$):", min_value=0.0, max_value=margem, step=0.01, key='valor')
                if valor > margem:
                    st.warning(f"O valor máximo liberado para você é de R$ {margem:,.2f}")
            else:
                valor = st.number_input("Valor solicitado (R$):", min_value=0.0, max_value=parcela_maxima, value=parcela_maxima, step=0.01, key='valor')
                if valor > parcela_maxima:
                    st.warning(f"O valor máximo liberado para você é de R$ {parcela_maxima:,.2f}")
            taxa_juros = st.number_input("Taxa de juros mensal (%):", min_value=0.0, step=0.01, key='taxa_juros', format="%f")
            if escolha == 'Empréstimo':
                parcelas = st.number_input("Quantidade de parcelas:", min_value=1, step=1, key='parcelas')
            else:
                parcelas = 1
                st.markdown('<p style="color: #7CB26E;">A quantidade de parcelas para antecipação salarial é sempre 1.</p>', unsafe_allow_html=True)

            if st.button('Calcular'):
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

                    if valor_prestacao_com_iof > parcela_maxima:
                        st.error(f"Sua parcela não pode ser maior que a parcela máxima de R$ {parcela_maxima:,.2f}. Simule novamente e tente aumentar a quantidade de parcelas em seu empréstimo.")
                    else:
                        # Adicionar espaço vazio na col2
                        with col2:
                            st.write("")
                            st.write("")
                            st.write("")
                            st.markdown(f'<p style="color: #7CB26E;">Valor solicitado: R$ {valor:,.2f}</p>', unsafe_allow_html=True)
                            st.markdown(f'<p style="color: #7CB26E;">Taxa de Juros: {taxa_juros}%</p>', unsafe_allow_html=True)
                            st.markdown(f'<p style="color: #7CB26E;">Quantidade de parcelas: {parcelas}</p>', unsafe_allow_html=True)

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
