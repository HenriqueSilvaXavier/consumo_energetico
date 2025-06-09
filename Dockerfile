FROM python:3.10-slim

# Define ambiente não interativo para evitar prompts do apt
ENV DEBIAN_FRONTEND=noninteractive

RUN \
  sed -i \
    -e 's|deb.debian.org|archive.debian.org|g' \
    -e 's|security.debian.org/debian-security .* updates|security.debian.org/debian-security bullseye-security|g' \
    /etc/apt/sources.list && \
  echo 'Acquire::Check-Valid-Until "false";' > /etc/apt/apt.conf.d/99no-check-valid-until && \
  apt-get update -o Acquire::AllowReleaseInfoChange=true && \
  apt-get install -y --no-install-recommends \
    openjdk-11-jre-headless \
    curl \
    git \
    ca-certificates && \
  rm -rf /var/lib/apt/lists/*

ENV JAVA_HOME="/usr/lib/jvm/java-11-openjdk-amd64"
ENV PATH="$JAVA_HOME/bin:$PATH"

ENV SPARK_VERSION=3.4.1
RUN curl -fsSL "https://downloads.apache.org/spark/spark-${SPARK_VERSION}/spark-${SPARK_VERSION}-bin-hadoop3.tgz" -o spark.tgz && \
    tar -xzf spark.tgz && \
    mv "spark-${SPARK_VERSION}-bin-hadoop3" /opt/spark && \
    rm spark.tgz

ENV SPARK_HOME=/opt/spark
ENV PATH=$SPARK_HOME/bin:$PATH
ENV PYSPARK_PYTHON=python3

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . /app
WORKDIR /app

EXPOSE 7860

CMD ["python", "app.py"]
