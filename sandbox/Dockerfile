FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
# Nenhuma dependência de terceiros na imagem base: stdlib pura.
# Projetos que precisarem de pacotes devem travar versões em requirements
# próprios e instalar aqui, nunca segredos.

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

RUN useradd --create-home --uid 10000 appuser \
 && install -d -m 0755 -o appuser -g appuser /work /tmp
USER appuser
WORKDIR /work

ENTRYPOINT ["python"]
CMD ["--version"]
