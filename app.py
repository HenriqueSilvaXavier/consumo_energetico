import gradio as gr
import json
import bcrypt
import pyotp
import qrcode
from io import BytesIO
from PIL import Image

from pyspark.sql import SparkSession
from pyspark.ml.feature import VectorAssembler
from pyspark.ml.regression import RandomForestRegressor
import pandas as pd
import matplotlib.pyplot as plt

import os
os.environ["JAVA_HOME"] = "C:\\Program Files\\Java\\jdk-11"

# --- Banco de dados de usuários ---
USERS_DB = "users.json"

def load_users():
    try:
        with open(USERS_DB, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_users(users):
    with open(USERS_DB, "w") as f:
        json.dump(users, f, indent=2)

def create_qr_code(uri):
    qr = qrcode.make(uri)
    buf = BytesIO()
    qr.save(buf)
    buf.seek(0)
    return Image.open(buf)

# --- Cadastro ---
def register(email, password):
    users = load_users()
    if email in users:
        return "Email já cadastrado.", None

    mfa_secret = pyotp.random_base32()
    uri = pyotp.totp.TOTP(mfa_secret).provisioning_uri(name=email, issuer_name="GradioApp")

    hashed_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    users[email] = {"password": hashed_pw, "mfa_secret": mfa_secret, "verified": False}
    save_users(users)

    return "Usuário criado! Escaneie o QR Code com Google Authenticator.", create_qr_code(uri)

# --- Login ---
def autenticar(email, senha):
    users = load_users()
    user = users.get(email)
    if not user:
        return "Usuário não encontrado.", False, "", False

    if not bcrypt.checkpw(senha.encode(), user["password"].encode()):
        return "Senha incorreta.", False, "", False

    return "Digite o token MFA", False, email, True

# --- Verificação MFA ---
def verificar_mfa(email, token):
    users = load_users()
    user = users.get(email)
    if not user:
        return "Usuário não encontrado.", False

    totp = pyotp.TOTP(user["mfa_secret"])
    if totp.verify(token):
        user["verified"] = True
        save_users(users)
        return "MFA verificado com sucesso! Faça login novamente.", True
    return "Token inválido.", False

# --- Páginas ---
def pagina_principal():
    return "Bem-vindo à página principal!"

def outra_pagina():
    return "Esta é outra interface."

# === Configuração Spark e ML ===
spark = SparkSession.builder.appName("PrevisaoTemperatura").getOrCreate()

df_pd = pd.read_csv(
    "/content/INMET_NE_PE_A301_RECIFE_01-01-2020_A_31-12-2020.CSV",
    encoding='latin1',
    sep=';',
    skiprows=8
)

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

df_spark = spark.createDataFrame(df_pd)

feature_cols = ["precipitacao", "pressao", "umidade", "hora", "mes"]
assembler = VectorAssembler(inputCols=feature_cols, outputCol="features")
df_ml = assembler.transform(df_spark).select("features", "temperatura")

train_data, test_data = df_ml.randomSplit([0.8, 0.2], seed=42)

rf = RandomForestRegressor(featuresCol="features", labelCol="temperatura", seed=42)
modelo = rf.fit(train_data)

predicoes = modelo.transform(test_data)
predicoes_pd = predicoes.select("temperatura", "prediction").toPandas()

# --- Funções gráficas ---
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

def prever_temperatura(precipitacao, pressao, umidade, hora, mes):
    entrada_df = pd.DataFrame([[precipitacao, pressao, umidade, hora, mes]], columns=feature_cols)
    entrada_spark = spark.createDataFrame(entrada_df)
    entrada_feat = assembler.transform(entrada_spark).select("features")
    pred = modelo.transform(entrada_feat).collect()[0]["prediction"]

    fig1, fig2, fig3 = gerar_graficos()
    return round(pred, 2), fig1, fig2, fig3

# === App Gradio com todas as interfaces ===
with gr.Blocks() as app:
    estado_login = gr.State(False)
    email_login = gr.State("")
    mostrar_mfa = gr.State(False)

    # Componentes MFA declarados uma vez
    mfa_email = gr.Textbox(label="Email", interactive=False, visible=False)
    mfa_token = gr.Textbox(label="Token MFA", visible=False)
    mfa_saida = gr.Text(visible=False)
    botao_mfa = gr.Button("Verificar MFA", visible=False)

    with gr.Tabs():
        with gr.Tab("Login"):
            login_email = gr.Textbox(label="Email")
            login_senha = gr.Textbox(label="Senha", type="password")
            login_botao = gr.Button("Login")
            login_saida = gr.Text()

            def atualiza_mfa_visibilidade(mfa_visivel, email):
                return (
                    gr.update(visible=mfa_visivel, value=email),
                    gr.update(visible=mfa_visivel),
                    gr.update(visible=mfa_visivel),
                    gr.update(visible=mfa_visivel)
                )

            login_botao.click(
                autenticar,
                inputs=[login_email, login_senha],
                outputs=[login_saida, estado_login, email_login, mostrar_mfa]
            ).then(
                atualiza_mfa_visibilidade,
                inputs=[mostrar_mfa, email_login],
                outputs=[mfa_email, mfa_token, mfa_saida, botao_mfa]
            )

        with gr.Tab("Cadastro"):
            cadastro_email = gr.Textbox(label="Email")
            cadastro_senha = gr.Textbox(label="Senha", type="password")
            botao_cadastro = gr.Button("Cadastrar")
            saida_cadastro = gr.Text()
            qr_code = gr.Image()

            botao_cadastro.click(
                register,
                inputs=[cadastro_email, cadastro_senha],
                outputs=[saida_cadastro, qr_code]
            )

        with gr.Tab("MFA"):
            def mfa_verificacao(email, token):
                msg, verificado = verificar_mfa(email, token)
                return msg, verificado

            botao_mfa.click(
                mfa_verificacao,
                inputs=[mfa_email, mfa_token],
                outputs=[mfa_saida, estado_login]
            )

        with gr.Tab("Interfaces"):
            mensagem = gr.Textbox(label="Status")
            principal = gr.Textbox(label="Principal")
            outra = gr.Textbox(label="Outra")

            def renderizar(pode_logar, email):
                if not pode_logar:
                    return "Faça login para ver os conteúdos", "", ""
                return f"Logado como {email}", pagina_principal(), outra_pagina()

            app.load(renderizar, inputs=[estado_login, email_login], outputs=[mensagem, principal, outra])

        with gr.Tab("Previsão de Temperatura"):
            input_precipitacao = gr.Slider(0, 50, label="Precipitação (mm)")
            input_pressao = gr.Slider(900, 1050, label="Pressão (mB)")
            input_umidade = gr.Slider(0, 100, label="Umidade (%)")
            input_hora = gr.Slider(0, 23, step=1, label="Hora do dia")
            input_mes = gr.Slider(1, 12, step=1, label="Mês")

            output_temp = gr.Number(label="Temperatura Prevista (°C)")
            output_graf1 = gr.Plot(label="Gráfico: Previsão Real x Prevista")
            output_graf2 = gr.Plot(label="Gráfico: Importância das Variáveis")
            output_graf3 = gr.Plot(label="Gráfico: Distribuição do Erro")

            btn_prever = gr.Button("Prever Temperatura")

            btn_prever.click(
                prever_temperatura,
                inputs=[input_precipitacao, input_pressao, input_umidade, input_hora, input_mes],
                outputs=[output_temp, output_graf1, output_graf2, output_graf3]
            )

app.launch()
