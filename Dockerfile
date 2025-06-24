#FROM python:3.10-slim

# update packages, install git and remove cache
#RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

#WORKDIR /app

#COPY requirements.txt .
#RUN pip install --no-cache-dir -r requirements.txt

#COPY . .

#ENTRYPOINT ["python", "main.py"]


FROM python:3.10-slim

# Установим git, curl (для Nodesource), Node.js и Mermaid CLI
RUN apt-get update \
 && apt-get install -y git curl ca-certificates \
 && curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
 && apt-get install -y nodejs \
 && npm install -g @mermaid-js/mermaid-cli \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENTRYPOINT ["python", "main.py"]
