FROM python:3.12

RUN curl -sSL https://pdm.fming.dev/install-pdm.py | python3 -
ADD . .
RUN /root/.local/bin/pdm install

CMD /root/.local/bin/pdm run litestar run --host 0.0.0.0 --port 8000
