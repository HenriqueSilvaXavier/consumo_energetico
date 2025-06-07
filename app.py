import gradio as gr
import json
import bcrypt
import pyotp
import qrcode
from io import BytesIO
from PIL import Image
import os

USERS_DB = "users.json"

# --- Helpers ---
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
def login(email, password):
    users = load_users()
    user = users.get(email)
    if not user:
        return "Usuário não encontrado.", False

    if not bcrypt.checkpw(password.encode(), user["password"].encode()):
        return "Senha incorreta.", False

    if not user["verified"]:
        return "Você precisa confirmar o MFA primeiro.", False

    return "Login bem-sucedido!", True

# --- Verifica MFA ---
def verificar_mfa(email, token):
    users = load_users()
    user = users.get(email)
    if not user:
        return "Usuário não encontrado."

    totp = pyotp.TOTP(user["mfa_secret"])
    if totp.verify(token):
        user["verified"] = True
        save_users(users)
        return "MFA verificado com sucesso! Faça login agora."
    return "Token inválido."

# --- Interfaces principais ---
def pagina_principal():
    return "Bem-vindo à página principal!"

def outra_pagina():
    return "Esta é outra interface."

# --- Interface Gradio ---
with gr.Blocks() as app:
    estado_login = gr.State(False)
    email_login = gr.State("")
    
    with gr.Tabs():
        with gr.Tab("Login"):
            with gr.Column():
                login_email = gr.Textbox(label="Email")
                login_senha = gr.Textbox(label="Senha", type="password")
                login_botao = gr.Button("Login")
                login_saida = gr.Text()

                def autenticar(email, senha):
                    msg, ok = login(email, senha)
                    return msg, ok, email if ok else ""
                
                login_botao.click(
                    autenticar,
                    inputs=[login_email, login_senha],
                    outputs=[login_saida, estado_login, email_login]
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
            mfa_email = gr.Textbox(label="Email")
            mfa_token = gr.Textbox(label="Token MFA")
            mfa_saida = gr.Text()
            botao_mfa = gr.Button("Verificar MFA")

            botao_mfa.click(
                verificar_mfa,
                inputs=[mfa_email, mfa_token],
                outputs=[mfa_saida]
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

# Lançamento do app
port = int(os.environ.get("PORT", 7860))
app.launch(server_name="0.0.0.0", server_port=port)

