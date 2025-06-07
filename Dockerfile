# Imagem base oficial do Python
FROM python:3.10-slim

# Define variáveis de ambiente
ENV PYSPARK_PYTHON=python3 \
    JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64 \
    PATH=$PATH:/usr/lib/jvm/java-11-openjdk-amd64/bin

# Instala dependências do sistema
RUN apt-get update && \
    apt-get install -y openjdk-11-jdk curl && \
    rm -rf /var/lib/apt/lists/*

# Copia os arquivos para o contêiner
WORKDIR /app
COPY . /app

# Instala dependências Python
RUN pip install --upgrade pip && pip install -r requirements.txt

# Expõe a porta do Gradio
EXPOSE 7860

# Comando para rodar o app Gradio
CMD ["python", "app.py"]
