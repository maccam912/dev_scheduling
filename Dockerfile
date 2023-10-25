FROM python:3.12

RUN curl -sSL https://pdm.fming.dev/install-pdm.py | python3 -
ADD . .
RUN pdm install

CMD pdm run litestar run --host 0.0.0.0 --port 8000
