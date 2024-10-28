FROM python:3.11
ARG DEBIAN_FRONTEND=noninteractive

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD [ "python", "./llmcord.py" ]
