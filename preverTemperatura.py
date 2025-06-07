from pyspark.sql import SparkSession
from pyspark.ml.feature import VectorAssembler
from pyspark.ml.regression import RandomForestRegressor
from pyspark.ml.evaluation import RegressionEvaluator
import pandas as pd
import matplotlib.pyplot as plt
import gradio as gr

# === Inicia Spark ===
spark = SparkSession.builder.appName("PrevisaoTemperatura").getOrCreate()

# === Carregamento e pré-processamento com Pandas ===
df_pd = pd.read_csv(
    "/content/INMET_NE_PE_A301_RECIFE_01-01-2020_A_31-12-2020.CSV",
    encoding='latin1',
    sep=';',
    skiprows=8
)
display(df_pd.head(20))

df_pd.columns = [col.strip() for col in df_pd.columns]
df_pd = df_pd.rename(columns={
    "TEMPERATURA DO AR - BULBO SECO, HORARIA (°C)": "temperatura",
    "PRECIPITAÇÃO TOTAL, HORÁRIO (mm)": "precipitacao",
    "PRESSAO ATMOSFERICA AO NIVEL DA ESTACAO, HORARIA (mB)": "pressao",
    "UMIDADE REL. MAX. NA HORA ANT. (AUT) (%)": "umidade"
})

df_pd[["pressao", "temperatura", "precipitacao"]] = df_pd[["pressao", "temperatura", "precipitacao"]].apply(
    lambda x: x.str.replace(',', '.').astype(float)
)

df_pd["datetime"] = pd.to_datetime(df_pd["Data"] + " " + df_pd["Hora UTC"], errors='coerce')
df_pd["hora"] = df_pd["datetime"].dt.hour
df_pd["mes"] = df_pd["datetime"].dt.month
df_pd = df_pd[["temperatura", "precipitacao", "pressao", "umidade", "hora", "mes"]].dropna()

# === Converte para PySpark ===
df_spark = spark.createDataFrame(df_pd)

# === Prepara dados para ML ===
feature_cols = ["precipitacao", "pressao", "umidade", "hora", "mes"]
assembler = VectorAssembler(inputCols=feature_cols, outputCol="features")
df_ml = assembler.transform(df_spark).select("features", "temperatura")

# === Divide dados ===
train_data, test_data = df_ml.randomSplit([0.8, 0.2], seed=42)

# === Modelo ===
rf = RandomForestRegressor(featuresCol="features", labelCol="temperatura", seed=42)
modelo = rf.fit(train_data)

# === Previsões iniciais ===
predicoes = modelo.transform(test_data)
predicoes_pd = predicoes.select("temperatura", "prediction").toPandas()
X_pd = df_pd[feature_cols]

# === Função para gerar gráficos ===
def gerar_graficos():
    fig1, ax1 = plt.subplots()
    ax1.scatter(predicoes_pd["temperatura"], predicoes_pd["prediction"], alpha=0.5)
    ax1.set_xlabel("Temperatura real")
    ax1.set_ylabel("Temperatura prevista")
    ax1.set_title("Previsão de Temperatura")

    fig2, ax2 = plt.subplots()
    importancias = modelo.featureImportances.toArray()
    ax2.barh(feature_cols, importancias, color="green")
    ax2.set_title("Importância das Variáveis")

    fig3, ax3 = plt.subplots()
    erros = predicoes_pd["temperatura"] - predicoes_pd["prediction"]
    ax3.hist(erros, bins=30, color="orange", edgecolor="black")
    ax3.set_title("Distribuição dos Erros")
    ax3.set_xlabel("Erro")

    return fig1, fig2, fig3

# === Função de previsão ===
def prever_temperatura(precipitacao, pressao, umidade, hora, mes):
    entrada_df = pd.DataFrame([[precipitacao, pressao, umidade, hora, mes]],
                              columns=feature_cols)
    entrada_spark = spark.createDataFrame(entrada_df)
    entrada_feat = assembler.transform(entrada_spark).select("features")
    pred = modelo.transform(entrada_feat).collect()[0]["prediction"]

    fig1, fig2, fig3 = gerar_graficos()
    return round(pred, 2), fig1, fig2, fig3

# === Interface Gradio ===
gr.Interface(
    fn=prever_temperatura,
    inputs=[
        gr.Slider(0, 50, label="Precipitação (mm)"),
        gr.Slider(900, 1050, label="Pressão (mB)"),
        gr.Slider(0, 100, label="Umidade (%)"),
        gr.Slider(0, 23, step=1, label="Hora do dia"),
        gr.Slider(1, 12, step=1, label="Mês")
    ],
    outputs=[
        gr.Number(label="Temperatura Prevista (°C)"),
        gr.Plot(label="Gráfico: Previsão Real x Prevista"),
        gr.Plot(label="Gráfico: Importância das Variáveis"),
        gr.Plot(label="Gráfico: Distribuição do Erro")
    ],
    title="Previsão de Temperatura com Random Forest (PySpark)",
    description="Ajuste os parâmetros e veja a previsão de temperatura e gráficos do modelo treinado com PySpark."
).launch()