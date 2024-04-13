FROM python:3.11-alpine AS builder
WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY ./testgram .
RUN chmod +x ./entrypoint.sh
ENTRYPOINT ["./entrypoint.sh"]