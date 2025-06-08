FROM python:3.10-slim

# Instala dependências de sistema (Java para Spark, utilitários)
RUN apt-get update && apt-get install -y \
    openjdk-11-jdk \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Define variáveis de ambiente para Java
ENV JAVA_HOME="/usr/lib/jvm/java-11-openjdk-amd64"
ENV PATH="$JAVA_HOME/bin:$PATH"

# Instala o Spark
ENV SPARK_VERSION=3.4.1
RUN curl -O https://downloads.apache.org/spark/spark-${SPARK_VERSION}/spark-${SPARK_VERSION}-bin-hadoop3.tgz && \
    tar -xzf spark-${SPARK_VERSION}-bin-hadoop3.tgz && \
    mv spark-${SPARK_VERSION}-bin-hadoop3 /opt/spark && \
    rm spark-${SPARK_VERSION}-bin-hadoop3.tgz

ENV SPARK_HOME=/opt/spark
ENV PATH=$SPARK_HOME/bin:$PATH
ENV PYSPARK_PYTHON=python3

# Instala as bibliotecas Python
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copia o código da aplicação
COPY . /app
WORKDIR /app

# Expõe a porta padrão do Gradio
EXPOSE 7860

# Comando para iniciar o app (ajuste para seu arquivo principal)
CMD ["python", "app.py"]
