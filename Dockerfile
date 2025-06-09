FROM debian:bullseye-slim

ENV DEBIAN_FRONTEND=noninteractive

# Repositórios oficiais do bullseye
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      ca-certificates \
      curl \
      git \
      openjdk-11-jre-headless \
      python3 \
      python3-pip && \
    rm -rf /var/lib/apt/lists/*

# Variáveis de ambiente Java
ENV JAVA_HOME="/usr/lib/jvm/java-11-openjdk-amd64"
ENV PATH="$JAVA_HOME/bin:$PATH"

# Instala Apache Spark
ENV SPARK_VERSION=3.4.1
RUN curl -fsSL "https://archive.apache.org/dist/spark/spark-${SPARK_VERSION}/spark-${SPARK_VERSION}-bin-hadoop3.tgz" -o spark.tgz && \
    tar -xzf spark.tgz && \
    mv "spark-${SPARK_VERSION}-bin-hadoop3" /opt/spark && \
    rm spark.tgz

ENV SPARK_HOME=/opt/spark
ENV PATH=$SPARK_HOME/bin:$PATH
ENV PYSPARK_PYTHON=python3

# Dependências Python
COPY requirements.txt .
RUN pip3 install --upgrade pip && pip3 install -r requirements.txt

# Código da aplicação
COPY . /app
WORKDIR /app

EXPOSE 7860
CMD ["python3", "app.py"]
