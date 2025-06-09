FROM python:3.10-slim

# Define ambiente não interativo para evitar prompts do apt
:contentReference[oaicite:1]{index=1}

RUN \
  # :contentReference[oaicite:2]{index=2}
  sed -i \
    :contentReference[oaicite:3]{index=3} \
    :contentReference[oaicite:4]{index=4} \
    :contentReference[oaicite:5]{index=5}
  # :contentReference[oaicite:6]{index=6}
  :contentReference[oaicite:7]{index=7}
  # :contentReference[oaicite:8]{index=8}
  :contentReference[oaicite:9]{index=9} \
  :contentReference[oaicite:10]{index=10} \
    :contentReference[oaicite:11]{index=11} \
    curl \
    git \
    ca-certificates && \
  :contentReference[oaicite:12]{index=12}

# Define variáveis de ambiente para o Java
:contentReference[oaicite:13]{index=13}
:contentReference[oaicite:14]{index=14}

# Instala o Apache Spark
:contentReference[oaicite:15]{index=15}
:contentReference[oaicite:16]{index=16} \
    :contentReference[oaicite:17]{index=17} \
    :contentReference[oaicite:18]{index=18} \
    :contentReference[oaicite:19]{index=19}

# Define variáveis de ambiente do Spark
:contentReference[oaicite:20]{index=20}
:contentReference[oaicite:21]{index=21}
:contentReference[oaicite:22]{index=22}

# Instala bibliotecas Python
:contentReference[oaicite:23]{index=23}
:contentReference[oaicite:24]{index=24}

# Copia o código da aplicação
COPY . /app
WORKDIR /app

# Expõe a porta padrão do Gradio
EXPOSE 7860

# Comando para iniciar a aplicação
:contentReference[oaicite:25]{index=25}
