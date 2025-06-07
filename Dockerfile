# Use uma imagem que já vem com Java e Python
FROM openjdk:11-slim

# Instala Python manualmente
RUN apt-get update && \
    apt-get install -y python3 python3-pip python3-venv && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Define Python como padrão
RUN ln -s /usr/bin/python3 /usr/bin/python

# Define diretório de trabalho
WORKDIR /app

# Copia arquivos
COPY . /app

# Instala dependências Python
RUN pip install --upgrade pip && pip install -r requirements.txt

# Expõe a porta padrão do Gradio
EXPOSE 7860

# Comando de inicialização
CMD ["python", "app.py"]
