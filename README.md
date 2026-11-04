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

## Installation Guide (Novo Servidor / Production)

### 1. Instalação do Plugin no Moodle
Clone o repositório na pasta de question types do seu Moodle:

```bash
cd /caminho/do/moodle/question/type
git clone https://github.com/leandrobocon/moodle-qtype_aitext_laya.git aitext
```

Instale também os dois comportamentos de questão obrigatórios (companion plugins):
```bash
cd /caminho/do/moodle/question/behaviour
git clone https://github.com/marcusgreen/moodle-qbehaviour_deferred_for_aitext.git deferred_for_aitext
git clone https://github.com/marcusgreen/moodle-qbehaviour_immediate_for_aitext.git immediate_for_aitext
```

Execute a atualização do banco de dados do Moodle:
```bash
php admin/cli/upgrade.php --non-interactive
```

### 2. Inicialização do Microsserviço Laya
No servidor onde o Laya será executado (pode ser o mesmo servidor do Moodle ou outro servidor na rede):

```bash
cd /caminho/do/moodle/question/type/aitext/service
docker compose up -d --build
```

O serviço Laya subirá na porta `8000`.

### 3. Configuração no Painel do Moodle
No Moodle, acesse como Administrador:
1. Vá para **Administração do Site ➔ Plugins ➔ Tipos de Questão ➔ AI Text Question** (`/admin/settings.php?section=qtypesettingaitext`).
2. Em **AI back end systems**, selecione: `Laya Decision Engine (Local)`.
3. Em **Laya Service Endpoint URL**, informe o endereço do serviço: `http://localhost:8000/v1/grade` (ou o IP/hostname do container, ex: `http://laya_service:8000/v1/grade`).
4. Em **Laya API Key / Bearer Token**, informe a chave cadastrada (ex: `sk-laya-local-actionandlearning`).
5. Clique em **Salvar alterações**.

Pronto! As questões do tipo AI Text já estarão corrigidas automaticamente pelo Laya.

---

## Credits
Thanks to the ByCS team for ongoing extensive feedback, support encouragement, testing and contributed code since around July 2024

## License

Licensed under the [GNU GPL v3 or later](https://www.gnu.org/licenses/gpl-3.0.html).