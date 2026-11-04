# Moodle AI Text Question Type

[![Moodle Plugin CI](https://github.com/marcusgreen/moodle-qtype_aitext/actions/workflows/moodle-ci.yml/badge.svg)](https://github.com/marcusgreen/moodle-qtype_aitext/actions/workflows/moodle-ci.yml)
[![GitHub Release](https://img.shields.io/github/release/marcusgreen/moodle-qtype_aitext.svg)](https://github.com/marcusgreen/moodle-qtype_aitext/releases)
[![Moodle Support](https://img.shields.io/badge/Moodle-%3E%3D%204.5-blue)](https://marketplace.moodle.com/plugins/qtype_aitext)

*by Marcus Green*

🇬🇧 **English** · 🇩🇪 **[Deutsch](./README.de.md)**

A Moodle question type that accepts free-text answers and grades them with a remote Large Language Model (LLM) such as ChatGPT or a self-hosted Ollama model. Each question defines its own grading prompt and optional marking scheme, so the AI evaluates responses against criteria you set.


For custom development and consultancy, contact Moodle Partner [Catalyst EU](https://www.catalyst-eu.net/).

Install from the Moodle plugins marketplace: <https://marketplace.moodle.com/plugins/qtype_aitext>

Changelog: <https://github.com/marcusgreen/moodle-qtype_aitext/blob/main/changelog.md>

Additional documentation: <https://github.com/marcusgreen/moodle-qtype_aitext/wiki>

## AI Backends

This fork supports four backend systems:

1. **Laya Decision Engine (Local)**: Fast, calibrated System 1 decision engine based on ModernBERT (`convaiinnovations/laya`). Eliminates LLM hallucinations, supports automated off-topic filtering (zeroing unrelated answers), and provides calibrated grading in ~35ms without external API costs. See [`service/README.md`](./service/README.md) for setup details.
2. **Core AI Subsystem**: Built into Moodle 4.5+ / 5.x.
3. **Local AI Manager**: mebis/ByCS AI integration.
4. **Tool AI Manager**: tool_aiconnect.

## Requirements

- Moodle 4.5 or later.
- Access to an AI backend (e.g. local Laya service or external LLM).

## How it works

You supply two things per question:

1. A **prompt** telling the AI how to evaluate the response.
2. An optional **marking scheme** describing how to award marks.

For the question *"Write an English sentence in the past tense"*, the prompt could be:

> Explain if there is anything wrong with the grammar in this text.

And a marking scheme could be:

> Give 10 marks if there are no errors, all spelling is correct and it is in the past tense. Give 0 marks if the grammar is incorrect. Deduct one mark for every word that is misspelled.

A **prompt tester** field in the question editing form uses AJAX to try prompts out directly, without stepping through the question preview screen.

## Grading

Grading runs through two dedicated companion question behaviours rather than overriding Moodle's core behaviours:

- [`qbehaviour_immediate_for_aitext`](https://github.com/marcusgreen/moodle-qbehaviour_immediate_for_aitext)
- [`qbehaviour_deferred_for_aitext`](https://github.com/marcusgreen/moodle-qbehaviour_deferred_for_aitext)

These are separate plugins and must be installed alongside this question type, under `question/behaviour/immediate_for_aitext` and `question/behaviour/deferred_for_aitext`. Without them, AIText questions cannot be graded.

This keeps AIText grading predictable and isolated from other question types. Existing quiz attempts that used the legacy `interactivecountback` behaviour are migrated automatically on upgrade; attempts belonging to other question types are left untouched.

If the configured AI tools are unavailable, grading degrades gracefully instead of erroring, so an attempt is not lost.

### Manual grading

AI-generated feedback can be shown to a human grader and used as a reference when marking a response manually.

## 📚 Guia de Instalação e Configuração (Novo Servidor / Produção)

Este guia orienta o provisionamento completo do plugin e do motor de decisão **Laya** em um novo servidor. A arquitetura é composta por:
1. **Microsserviço Laya:** API local de alta performance baseada em System 1 (ModernBERT + RLCD) que avalia o texto sem gerar alucinações.
2. **Plugin Moodle (`qtype_aitext`):** O tipo de questão dissertativa com IA.
3. **Question Behaviours:** Os 2 companion plugins necessários para o ciclo de vida da tentativa no Moodle.

---

### Passo 1: Subir o Microsserviço Laya

O serviço do Laya pode rodar no mesmo host do Moodle ou em outro servidor conectado via rede/Docker.

#### Opção A: Via Docker Compose (Recomendado)
```bash
# 1. Acesse a pasta do serviço
cd /caminho/do/repositorio/service

# 2. Inicie o container
docker compose up -d --build

# 3. Verifique os logs e a inicialização
docker compose logs -f
```

#### Opção B: Via Docker Run (Sem Compose)
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

#### Teste de Saúde do Serviço
Após inicializar, valide se a API está respondendo:
```bash
curl http://localhost:8000/health
# Resposta esperada: {"status": "healthy", "service": "laya-decision-engine", ...}
```

---

### Passo 2: Instalar os Plugins no Moodle

O Moodle requer o plugin principal e dois comportamentos de tentativa (`qbehaviour`):

1. **Instalar o tipo de questão (`qtype_aitext`):**
   ```bash
   cd /caminho/do/moodle/public/question/type
   git clone https://github.com/leandrobocon/moodle-qtype_aitext_laya.git aitext
   chown -R www-data:www-data aitext
   ```

2. **Instalar os question behaviours obrigatórios:**
   ```bash
   cd /caminho/do/moodle/public/question/behaviour
   git clone https://github.com/marcusgreen/moodle-qbehaviour_deferred_for_aitext.git deferred_for_aitext
   git clone https://github.com/marcusgreen/moodle-qbehaviour_immediate_for_aitext.git immediate_for_aitext
   chown -R www-data:www-data deferred_for_aitext immediate_for_aitext
   ```

3. **Executar a atualização do banco de dados do Moodle:**
   ```bash
   sudo -u www-data php /caminho/do/moodle/public/admin/cli/upgrade.php --non-interactive
   ```

---

### Passo 3: Configurar o Laya no Painel do Moodle

1. Acesse o Moodle com uma conta de Administrador.
2. Acesse: **Administração do Site ➔ Plugins ➔ Tipos de Questão ➔ AI Text Question**  
   *(Ou acesse diretamente a URL: `/admin/settings.php?section=qtypesettingaitext`)*
3. Defina os parâmetros:
   - **AI back end systems:** Selecione `Laya Decision Engine (Local)`
   - **Laya Service Endpoint URL:**
     - Se o Moodle e o Laya estiverem na mesma rede Docker: `http://laya_service:8000/v1/grade`
     - Se estiverem no mesmo servidor físico (fora do Docker): `http://127.0.0.1:8000/v1/grade`
     - Se estiverem em servidores separados na rede interna: `http://<IP_DO_SERVIDOR_LAYA>:8000/v1/grade`
   - **Laya API Key / Bearer Token:** `sk-laya-local-actionandlearning` (ou a chave configurada no `.env` do serviço)
4. Clique em **Salvar alterações**.

---

### Passo 4: Segurança de Rede do Moodle (cURL Security)

Por padrão de segurança, o Moodle bloqueia conexões cURL para endereços de rede privada e loopback (`127.0.0.1`, `172.x.x.x`, etc.), o que pode causar o erro *"Esta URL está bloqueada"*.

Para liberar o acesso ao microsserviço Laya:
1. Acesse: **Administração do Site ➔ Segurança ➔ Segurança HTTP** (`/admin/settings.php?section=httpsecurity`).
2. No campo **Hosts permitidos (cURL allowed hosts)**, adicione o hostname ou IP do Laya:
   ```text
   laya_service
   127.0.0.1
   172.16.0.0/12
   localhost
   ```
3. Salve as alterações.

---

### Passo 5: Regras de Avaliação do Motor Laya

O motor Laya configurado neste repositório opera sob calibração pedagógica ativa:
- 🚫 **Fora de Contexto (Off-Topic):** Respostas que tratam de temas alheios à questão (ex: culinária, esportes, piadas, futebol) são detectadas em primeira camada e **zeradas imediatamente (0.0 / 100)**.
- 🎯 **Respostas Completas e Articuladas:** Respostas que explicam os conceitos fundamentais e exemplificam com ferramentas práticas reais (ex: fóruns, wikis, questionários) são bonificadas com a **nota máxima (100.0 / 100)**.
- 📝 **Respostas Parciais:** Respostas conceituais sem exemplificação de ferramentas recebem nota proporcional e feedback formativo orientado.

---

## Credits
Thanks to the ByCS team for ongoing extensive feedback, support encouragement, testing and contributed code since around July 2024

## License

Licensed under the [GNU GPL v3 or later](https://www.gnu.org/licenses/gpl-3.0.html).