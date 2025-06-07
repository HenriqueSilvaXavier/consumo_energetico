FROM python:3.10-slim

# Instala dependências do sistema
RUN apt-get update && apt-get install -y openjdk-11-jdk curl && \
    rm -rf /var/lib/apt/lists/*

# Variáveis de ambiente para Java e Spark
ENV JAVA_HOME="/usr/lib/jvm/java-11-openjdk-amd64"
ENV PATH="$JAVA_HOME/bin:$PATH"

# Instala o Spark manualmente
ENV SPARK_VERSION=3.4.1
RUN curl -O https://downloads.apache.org/spark/spark-$SPARK_VERSION/spark-$SPARK_VERSION-bin-hadoop3.tgz && \
    tar -xzf spark-$SPARK_VERSION-bin-hadoop3.tgz && \
    mv spark-$SPARK_VERSION-bin-hadoop3 /opt/spark && \
    rm spark-$SPARK_VERSION-bin-hadoop3.tgz

ENV SPARK_HOME=/opt/spark
ENV PATH=$SPARK_HOME/bin:$PATH
ENV PYSPARK_PYTHON=python3

# Instala as libs Python
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copia o app
COPY . /app
WORKDIR /app

CMD ["python", "app.py"]
