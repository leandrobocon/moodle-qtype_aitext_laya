# Laya Decision Engine Microservice for Moodle

Este microsserviço expõe o **Laya** (`NandhaKishorM/laya` / `convaiinnovations/laya`) via HTTP para correção automatizada de questões dissertativas no Moodle através do plugin `qtype_aitext_laya`.

---

## 🚀 Como subir o serviço em um novo servidor

### Opção 1: Usando Docker Compose (Recomendado)

1. Entre na pasta `service`:
   ```bash
   cd service
   ```

2. Inicie o container:
   ```bash
   docker compose up -d --build
   ```

3. Verifique o status e logs:
   ```bash
   docker compose logs -f
   ```

O serviço estará escutando na porta `8000`.

---

### Opção 2: Usando Docker diretamente

```bash
docker run -d \
  --name laya_service \
  --restart unless-stopped \
  -p 8000:8000 \
  -e LAYA_PORT=8000 \
  -e LAYA_API_KEY="sk-laya-local-actionandlearning" \
  -v laya_cache:/root/.cache/huggingface \
  python:3.12-slim bash -c "
    pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir laya && \
    python3 /app/server.py
  "
```

---

### Opção 3: Usando Python / Virtualenv diretamente no Host

1. Requisitos: Python 3.12 ou 3.13.
2. Criar ambiente virtual:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
3. Instalar dependências:
   ```bash
   pip install torch --index-url https://download.pytorch.org/whl/cpu
   pip install laya
   ```
4. Executar o servidor:
   ```bash
   export LAYA_PORT=8000
   export LAYA_API_KEY="sk-laya-local-actionandlearning"
   python3 server.py
   ```

---

## 📡 Endpoints Disponíveis

| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/health` | Checagem de integridade do serviço |
| `POST` | `/v1/grade` | Endpoint principal de correção para o Moodle |
| `POST` | `/v1/systemone` | Protocolo nativo System 1 do Laya |
| `POST` | `/v1/chat/completions` | Compatibilidade com o formato OpenAI |

### Exemplo de Teste de Correção:
```bash
curl -X POST http://localhost:8000/v1/grade \
  -H "Authorization: Bearer sk-laya-local-actionandlearning" \
  -H "Content-Type: application/json" \
  -d '{
    "response": "O Moodle promove a aprendizagem ativa através de fóruns e wikis.",
    "questiontext": "Explique como o Moodle pode ser utilizado para promover o aprendizado ativo e colaborativo.",
    "defaultmark": 100.0
  }'
```
