FROM python:alpine

WORKDIR /app

RUN apk update && apk add --no-cache bash

RUN pip install \
    "discord.py>=2.3.2" \
    litellm \
    python-dotenv

COPY . /app
RUN cp /app/.env.example /app/.env
RUN chown -R 1000:1000 /app
USER 1000

CMD ["bash", "run.sh"]
