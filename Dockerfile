# Dockerfile com versão fixada do Python e execução segura via usuário não-root
FROM python:3.12.9-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PORT=8000

# Criação de grupo e usuário de sistema não-root (UID/GID 10001)
RUN groupadd -g 10001 appgroup && \
    useradd -u 10001 -g appgroup -s /bin/sh -m appuser

WORKDIR /app

# Criação do diretório de dados para persistência do SQLite com permissões adequadas
RUN mkdir -p /app/data && chown -R appuser:appgroup /app

# Cópia dos manifestos de dependência
COPY --chown=appuser:appgroup pyproject.toml README.md /app/

# Instalação das dependências de produção
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir .

# Cópia do código-fonte da aplicação
COPY --chown=appuser:appgroup app /app/app

# Alterna para o usuário não-root por segurança
USER 10001:10001

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/saude')" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
