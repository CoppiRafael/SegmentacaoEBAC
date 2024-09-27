import pandas as pd
import numpy as np
from datetime import datetime
import streamlit as st
import plotly.express as px

# Função para formatar o texto em azul com centralização.
def format_blue(text: str) -> str:
    st.markdown(
        f"""
        <div style="text-align: center;">
            <h1 style="color: #3498db;">{text}</h1>
        </div>
        """,
        unsafe_allow_html=True
    )

# Carregamento de dados com cache para evitar recarregamento contínuo ao interagir com o app.
@st.cache_data
def load_data(file_data):
    try:
        return pd.read_csv(file_data, parse_dates=['DiaCompra'])
    except:
        return pd.read_excel(file_data)

# Função para classificar a recência em quartis.
def recencia_class(x, r, q_dict):
    if x <= q_dict[r][0.25]:
        return "A"
    elif x <= q_dict[r][0.5]:
        return 'B'
    elif x <= q_dict[r][0.75]:
        return 'C'
    else:
        return 'D'

# Função para classificar a frequência e valor em quartis.
def freq_val_class(x, fv, q_dict):
    if x <= q_dict[fv][0.25]:
        return "D"
    elif x <= q_dict[fv][0.5]:
        return 'C'
    elif x <= q_dict[fv][0.75]:
        return 'B'
    else:
        return 'A'

def main():
    st.set_page_config(page_title="Payouts Analysis",
                       layout='wide',
                       initial_sidebar_state='expanded')
    # Título principal do app

    st.markdown(
        """
        <div style="text-align: center;">
            <h1 style="color: #3498db;">RFV</h1>
            <h3>Recência - Frequência - Valor</h3>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Introdução ao conceito de RFV
    st.info("""RFV (Recência, Frequência, Valor) é utilizado para segmentar clientes com base no comportamento de compras. 
            Cada cliente é classificado em relação a esses três fatores, o que permite criar ações de marketing mais eficazes.""")

    st.write("""
    - **Recência (R)**: Quantos dias se passaram desde a última compra.
    - **Frequência (F)**: Número total de compras em um determinado período.
    - **Valor (V)**: Valor total gasto pelos clientes no período.
    """)

    # Upload de arquivo via barra lateral
    st.sidebar.markdown(
        """
        <div style="text-align: center;">
            <h1 style="color: #3498db;">RFV</h1>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.sidebar.write("## Carregue o arquivo de dados aqui")

    data_file_1 = st.sidebar.file_uploader("", type=['csv', 'xlsx'])

    # Verificação do upload de arquivo
    if data_file_1 is not None:
        df_compras = load_data(data_file_1)
        st.write(f"*O dataset contém {df_compras.shape[0]} linhas e {df_compras.shape[1]} colunas*")
        
        # Exibição dos dados carregados
        st.subheader("Visualização dos Dados")
        st.write(df_compras)

        # Definindo a data atual para o cálculo de recência
        today_aula = datetime(2021, 12, 9)

        # Cálculo da Recência
        format_blue("Recência:")
        st.write('Quantos dias se passaram desde a última compra de cada cliente?')
        df_recencia = df_compras.groupby('ID_cliente')['DiaCompra'].max().reset_index().rename(columns={'DiaCompra':'DiaUltimaCompra'})
        df_recencia['Recencia'] = df_recencia['DiaUltimaCompra'].apply(lambda x: (today_aula - x).days)
        df_recencia.drop(columns=['DiaUltimaCompra'], inplace=True)
        st.write(df_recencia)

        # Cálculo da Frequência
        format_blue("Frequência:")
        st.write('Quantas compras cada cliente realizou no período?')
        df_freq = df_compras.groupby('ID_cliente')['CodigoCompra'].count().reset_index().rename(columns={'CodigoCompra': "Frequencia"})
        st.write(df_freq)

        # Cálculo do Valor Total
        format_blue('Valor:')
        st.write('Qual o valor total gasto por cada cliente?')
        df_valor = df_compras.groupby('ID_cliente')['ValorTotal'].sum().reset_index()
        st.write(df_valor)

        # Combinando Recência, Frequência e Valor em um único DataFrame
        format_blue("RFV:")
        df_RF = df_recencia.merge(df_valor, on='ID_cliente')
        df_RFV = df_RF.merge(df_freq, on='ID_cliente')
        st.write(df_RFV)

        # Cálculo dos quartis para segmentação
        quartis = df_RFV.quantile(q=[0.25, 0.5, 0.75])

        # Visualização dos DataFrames lado a lado
        st.write("### Visualização lado a lado dos DataFrames:")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            format_blue('(R)')
            st.write(df_recencia)
        with col2:
            format_blue('(F)')
            st.write(df_freq)
        with col3:
            format_blue('(V)')
            st.write(df_valor)
        with col4:
            format_blue('(RFV)')
            st.write(df_RFV)

        # Classificação dos clientes com base em Recência, Frequência e Valor
        df_RFV['R_Quartile'] = df_RFV['Recencia'].apply(recencia_class, args=("Recencia", quartis))
        df_RFV['F_Quartile'] = df_RFV['Frequencia'].apply(freq_val_class, args=("Frequencia", quartis))
        df_RFV['V_Quartile'] = df_RFV['ValorTotal'].apply(freq_val_class, args=("ValorTotal", quartis))
        df_RFV.set_index('ID_cliente', inplace=True)

        # Exibição da Tabela Segmentada
        format_blue("Segmentação utilizando o RFV:")
        st.write(df_RFV)

        # Cálculo do RFV Score e exibição
        df_RFV['RFV_Score'] = df_RFV['R_Quartile'] + df_RFV['F_Quartile'] + df_RFV['V_Quartile']
        format_blue('Tabela com RFV Score:')
        st.write(df_RFV)

        # Exibição dos top 10 clientes com melhor pontuação RFV
        st.write("### Top 10 clientes com pontuação 'AAA':")
        st.write(df_RFV[df_RFV['RFV_Score'] == 'AAA'].sort_values("ValorTotal", ascending=False).head(10))

        # Exibição da quantidade de clientes por grupo RFV Score
        st.subheader('Quantidade de clientes por grupo RFV:')
        col1, col2 = st.columns(2)
        with col2:
            st.write(df_RFV['RFV_Score'].value_counts())
        with col1:
            fig = px.bar(df_RFV, x='RFV_Score', title="Distribuição de RFV Score")
            st.plotly_chart(fig)

        # Adicionando possíveis ações de marketing para cada grupo RFV
        format_blue('Exemplo de Ações de Marketing/CRM:')
        st.markdown("""
```python
dict_acoes = {
    'AAA': 'Enviar cupons de desconto e amostras grátis para novos produtos.',
    'DDD': 'Identificar possíveis churns e implementar ações de recuperação.',
    'DAA': 'Enviar ofertas e promoções para reativar clientes.',
    'CAA': 'Enviar promoções personalizadas para aumentar a retenção.'
}
```""")

        dict_acoes = {
            'AAA': 'Enviar cupons de desconto e amostras grátis para novos produtos.',
            'DDD': 'Churn! Clientes com pouco gasto e poucas compras.',
            'DAA': 'Enviar ofertas e promoções para reativar clientes.',
            'CAA': 'Enviar promoções personalizadas para aumentar a retenção.'
        }
        df_RFV["Acoes_de_Marketing/CRM"] = df_RFV['RFV_Score'].map(dict_acoes)
        st.write(df_RFV)

        # Botão para salvar o arquivo em Excel
        if st.button('Salvar tabela como arquivo Excel'):
            df_RFV.to_excel("RFV.xlsx")
            st.success("Arquivo Excel salvo com sucesso!")

if __name__ == '__main__':
    main()
