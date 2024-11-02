FROM python:3.12-slim
ARG DEBIAN_FRONTEND=noninteractive

WORKDIR /usr/src/app

RUN pip install --no-cache-dir discord.py httpx openai

CMD [ "python", "llmcord.py" ]
