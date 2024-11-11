FROM python:3.12-slim
ARG DEBIAN_FRONTEND=noninteractive

WORKDIR /usr/src/app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "llmcord.py"]
