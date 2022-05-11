FROM python:3.7.11-alpine3.14

ENV DOCKER=True

WORKDIR /app

COPY requirements.txt /tmp/
RUN pip3 install --requirement /tmp/requirements.txt

COPY sctool ./
COPY /config ./config
COPY /helpers ./helpers
COPY /src ./src

CMD ["sh", "-c", "./sctool"]