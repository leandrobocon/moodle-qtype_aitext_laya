FROM python:3.12-slim

WORKDIR /app

# Instala dependências essenciais (PyTorch versão CPU leve + Laya Decision Engine)
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir laya

COPY server.py /app/server.py

ENV LAYA_PORT=8000 \
    LAYA_API_KEY="sk-laya-local-actionandlearning"

VOLUME ["/root/.cache/huggingface"]

EXPOSE 8000

CMD ["python3", "/app/server.py"]
