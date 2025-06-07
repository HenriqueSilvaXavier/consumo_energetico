import pandas as pd
import matplotlib.pyplot as plt
from statsmodels.tsa.seasonal import seasonal_decompose
import io
import base64

# Função para converter gráfico para <img>
def fig_to_base64_img(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    img_base64 = base64.b64encode(buf.read()).decode('utf-8')
    return f'<img src="data:image/png;base64,{img_base64}"/>'

# Ler e preparar dados
df = pd.read_csv('CONSUMO_energia.csv', sep=';', header=5)
meses = ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ']

def preparar_ano(df, ano, regiao='Nordeste'):
    linha = df[df['Unnamed: 0'] == regiao].iloc[0]
    valores = linha[meses].values
    df_ano = pd.DataFrame({'Mes': meses, 'Consumo_MWh': valores})
    df_ano['Consumo_MWh'] = df_ano['Consumo_MWh'].replace('', pd.NA)
    df_ano['Consumo_MWh'] = df_ano['Consumo_MWh'].str.replace('.', '', regex=False)
    df_ano['Consumo_MWh'] = pd.to_numeric(df_ano['Consumo_MWh'], errors='coerce')
    df_ano['Mes_num'] = df_ano['Mes'].map({m: i+1 for i, m in enumerate(meses)})
    df_ano['Data'] = pd.to_datetime({'year': ano, 'month': df_ano['Mes_num'], 'day': 1})
    df_ano = df_ano.set_index('Data')
    return df_ano[['Consumo_MWh']]

# Dados
df_2020 = preparar_ano(df, 2020)
df_2021 = preparar_ano(df, 2021)
df_ne_2anos = pd.concat([df_2020, df_2021])
df_ne_2anos['Consumo_MWh'] = df_ne_2anos['Consumo_MWh'].interpolate()

# Gráfico 1 – Decomposição Sazonal
result = seasonal_decompose(df_ne_2anos['Consumo_MWh'], model='additive', period=12)
fig1 = result.plot()
img1 = fig_to_base64_img(fig1)

# Gráfico 2 – Padrão médio mensal
seasonal_monthly = result.seasonal.groupby(result.seasonal.index.month).mean()
fig2, ax2 = plt.subplots(figsize=(10,5))
ax2.bar(seasonal_monthly.index, seasonal_monthly, color='green')
ax2.set_title('Padrão Sazonal Médio Mensal do Consumo de Energia - Nordeste')
ax2.set_xlabel('Mês')
ax2.set_ylabel('Sazonalidade Média (Consumo MWh)')
ax2.set_xticks(seasonal_monthly.index)
ax2.set_xticklabels(meses)
ax2.grid(axis='y')
img2 = fig_to_base64_img(fig2)

# Gráfico 3 – Sazonalidade por estação
df_sazonal = result.seasonal.reset_index()
df_sazonal.columns = ['Data', 'Sazonalidade']
df_sazonal['Ano'] = df_sazonal['Data'].dt.year
df_sazonal['Mês'] = df_sazonal['Data'].dt.month

def mes_para_estacao(mes):
    if mes in [12, 1, 2]: return 'Verão'
    elif mes in [3, 4, 5]: return 'Outono'
    elif mes in [6, 7, 8]: return 'Inverno'
    else: return 'Primavera'

df_sazonal['Estação'] = df_sazonal['Mês'].apply(mes_para_estacao)
df_pivot = df_sazonal.groupby(['Ano', 'Estação'])['Sazonalidade'].mean().unstack()
df_pivot = df_pivot[['Verão', 'Outono', 'Inverno', 'Primavera']]

fig3 = plt.figure(figsize=(10,6))
df_pivot.plot(kind='bar', stacked=True, colormap='viridis', ax=plt.gca())
plt.title('Sazonalidade Média Empilhada por Estação e Ano - Nordeste')
plt.ylabel('Sazonalidade Média (Consumo MWh)')
plt.xlabel('Ano')
plt.legend(title='Estação')
plt.grid(axis='y')
img3 = fig_to_base64_img(fig3)

# Criar HTML com os gráficos
html = f"""
<html>
<head><title>Gráficos de Consumo de Energia</title></head>
<body>
<h1>Decomposição Sazonal</h1>
{img1}
<h1>Padrão Sazonal Médio Mensal</h1>
{img2}
<h1>Sazonalidade Média por Estação</h1>
{img3}
</body>
</html>
"""

# Salvar como arquivo
with open('graficos_consumo.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("Arquivo HTML gerado com sucesso.")
