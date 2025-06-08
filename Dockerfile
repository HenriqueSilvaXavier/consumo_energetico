FROM python:3.10-slim

# Define ambiente não interativo para evitar prompts
ENV DEBIAN_FRONTEND=noninteractive

# Atualiza repositórios e instala dependências do sistema (incluindo Java)
RUN apt-get update --allow-releaseinfo-change && apt-get install -y \
    openjdk-11-jre-headless \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Define variáveis de ambiente para o Java
ENV JAVA_HOME="/usr/lib/jvm/java-11-openjdk-amd64"
ENV PATH="$JAVA_HOME/bin:$PATH"

# Instala o Apache Spark
ENV SPARK_VERSION=3.4.1
RUN curl -fsSL https://downloads.apache.org/spark/spark-${SPARK_VERSION}/spark-${SPARK_VERSION}-bin-hadoop3.tgz -o spark.tgz && \
    tar -xzf spark.tgz && \
    mv spark-${SPARK_VERSION}-bin-hadoop3 /opt/spark && \
    rm spark.tgz

# Define variáveis de ambiente do Spark
ENV SPARK_HOME=/opt/spark
ENV PATH=$SPARK_HOME/bin:$PATH
ENV PYSPARK_PYTHON=python3

# Instala bibliotecas Python
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copia o código da aplicação
COPY . /app
WORKDIR /app

# Expõe a porta padrão do Gradio
EXPOSE 7860

# Comando para iniciar a aplicação (ajuste se necessário)
CMD ["python", "app.py"]
