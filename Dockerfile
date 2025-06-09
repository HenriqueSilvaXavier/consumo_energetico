FROM debian:bullseye-slim

ENV DEBIAN_FRONTEND=noninteractive

# 1) Dependências de sistema  ────────────────────────────────────────────────
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        ca-certificates curl git \
        openjdk-11-jre-headless \
        python3 python3-pip \
        procps                # ← fornece o comando `ps`, exigido pelo Spark \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# 2) Java
ENV JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
ENV PATH=$JAVA_HOME/bin:$PATH

# 3) Spark
ENV SPARK_VERSION=3.4.1
RUN curl -fsSL https://archive.apache.org/dist/spark/spark-${SPARK_VERSION}/spark-${SPARK_VERSION}-bin-hadoop3.tgz \
      -o /tmp/spark.tgz && \
    tar -xzf /tmp/spark.tgz -C /opt && \
    mv /opt/spark-${SPARK_VERSION}-bin-hadoop3 /opt/spark && \
    rm /tmp/spark.tgz
ENV SPARK_HOME=/opt/spark
ENV PATH=$SPARK_HOME/bin:$PATH
ENV PYSPARK_PYTHON=python3   # garante que o executável python certo seja usado

# 4) Python
COPY requirements.txt .
RUN pip3 install --no-cache-dir --upgrade pip && \
    pip3 install --no-cache-dir -r requirements.txt

# 5) Código da aplicação
COPY . /app
WORKDIR /app

# 6) Expor a porta (Railway injeta variável $PORT)
EXPOSE 7860
CMD ["python3", "app.py"]
