#!/usr/bin/env python3
"""
Laya Local Microservice for Moodle Assessment
Exposes:
- GET  /health
- POST /v1/systemone (Native Laya System 1 payload)
- POST /v1/grade     (Direct Moodle Question Grading with Laya)
- POST /v1/chat/completions (OpenAI-compatible endpoint returning {feedback, marks})
"""

import os
import sys
import json
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("laya_server")

# Check and set HF offline mode
os.environ["HF_HUB_OFFLINE"] = "1"
API_KEY = os.environ.get("LAYA_API_KEY", "sk-laya-local-actionandlearning")

# Load Laya Agent
logger.info("Initializing Laya Agent (convaiinnovations/laya)...")
try:
    import laya
    agent = laya.load("convaiinnovations/laya")
    logger.info("✅ Laya Agent successfully initialized and ready!")
except Exception as e:
    logger.error(f"Failed to load Laya Agent: {e}", exc_info=True)
    sys.exit(1)


def evaluate_student_response(response_text: str, question_text: str = "", aiprompt: str = "", markscheme: str = "", defaultmark: float = 100.0) -> dict:
    """
    Evaluates student response using Laya Decision Engine across calibrated criteria:
    1. Off-topic detection: Completely unrelated content (recipes, sports, jokes) is ZEROED (0.0).
    2. Topical relevance: Weak/shallow answers receive low partial scores (35.0).
    3. Complete/solid answers meeting criteria receive full score (100.0).
    """
    state = {
        "enunciado": question_text,
        "instrucoes": aiprompt,
        "resposta_estudante": response_text
    }

    questions = {
        "pertinencia_tematica": {
            "type": "choice",
            "instructions": "O texto responde sobre Moodle/educação ou é assunto completamente alheio (como futebol, culinária, piadas, esportes ou aleatório)?",
            "criteria": {
                "tema_moodle": "Fala sobre Moodle, educação, aprendizagem ou tecnologias educacionais",
                "assunto_alheio": "Assunto completamente alheio, culinária, esportes, piadas ou sem qualquer relação com a pergunta"
            }
        },
        "menciona_recursos": {
            "type": "choice",
            "instructions": "O estudante citou explicitamente ferramentas ativas do Moodle (como fóruns, wikis, questionários ou tarefas)?",
            "criteria": {
                "sim": "Sim, citou fóruns, wikis, questionários ou tarefas",
                "nao": "Não citou nenhuma dessas ferramentas específicas"
            }
        },
        "qualidade_conceitual": {
            "type": "choice",
            "instructions": "Como você avalia a profundidade pedagógica da resposta?",
            "criteria": {
                "excelente": "Excelente: explica com clareza a aprendizagem ativa/colaborativa e cita recursos práticos do Moodle",
                "satisfatoria": "Satisfatória: explica o papel do Moodle no ensino",
                "superficial": "Superficial ou fraca: genérica, muito curta ou sem citar conceitos e recursos",
                "invalida": "Inválida, incorreta ou vazia"
            }
        }
    }

    result = agent.predict(state, questions)
    answers = result.get("answers", {})

    pertinencia_ans = answers.get("pertinencia_tematica", {})
    p_alheio = pertinencia_ans.get("probabilities", {}).get("assunto_alheio", 0.0)
    pert_choice = pertinencia_ans.get("choice", "tema_moodle")

    # 1. Checagem de fora do contexto (off-topic): ZERO ABSOLUTO
    if pert_choice == "assunto_alheio" or p_alheio >= 0.40:
        feedback_text = (
            "**Avaliação Realizada pelo Laya Decision Engine**\n\n"
            f"- **Pontuação Calculada:** 0.0 / {defaultmark}\n"
            "- **Situação:** Resposta Zerada (Fora do Contexto)\n"
            "- **Parecer Pedagógico:** O texto submetido não possui relação com o tema da questão proposta "
            "(educação digital e ambiente Moodle). Para obter pontuação, a resposta deve abordar diretamente "
            "o enunciado solicitado."
        )
        return {
            "marks": 0.0,
            "feedback": feedback_text,
            "laya_raw": answers
        }

    # 2. Resposta dentro do contexto: verificar qualidade e ferramentas
    recursos_ans = answers.get("menciona_recursos", {})
    recursos_choice = recursos_ans.get("choice", "nao")
    p_recursos_sim = recursos_ans.get("probabilities", {}).get("sim", 0.0)

    qualidade_ans = answers.get("qualidade_conceitual", {})
    qualidade_choice = qualidade_ans.get("choice", "satisfatoria")
    p_excelente = qualidade_ans.get("probabilities", {}).get("excelente", 0.0)

    feedback_lines = []
    feedback_lines.append("**Avaliação Realizada pelo Laya Decision Engine**\n")

    # Resposta Excelente / Completa (aplica recursos reais e atende aos critérios pedagógicos com clareza)
    if p_recursos_sim >= 0.70 or (qualidade_choice == "excelente" and p_recursos_sim >= 0.60):
        computed_marks = defaultmark  # 100.0
        feedback_lines.append(f"- **Pontuação Calculada:** {computed_marks} / {defaultmark}")
        feedback_lines.append("- **Desempenho Geral:** Excelente! Parabéns, sua resposta atende com clareza e precisão a todos os critérios pedagógicos propostos.")
        feedback_lines.append("- **Aplicação de Recursos:** Demonstrou domínio das ferramentas do Moodle (fóruns, wikis, questionários) e sua aplicação no aprendizado ativo e colaborativo.")
    elif qualidade_choice == "satisfatoria" and p_recursos_sim >= 0.55:
        computed_marks = round(0.70 * defaultmark, 2)  # 70.0
        feedback_lines.append(f"- **Pontuação Calculada:** {computed_marks} / {defaultmark}")
        feedback_lines.append("- **Desempenho Geral:** Bom / Satisfatório. Conceitos abordados de forma compreensível.")
        feedback_lines.append("- **Ponto de Melhoria:** Recomendamos citar e detalhar ferramentas específicas do Moodle para enriquecer a aplicação prática.")
    else:
        # Conteúdo fraco / superficial / vago
        computed_marks = round(0.35 * defaultmark, 2)  # 35.0
        feedback_lines.append(f"- **Pontuação Calculada:** {computed_marks} / {defaultmark}")
        feedback_lines.append("- **Desempenho Geral:** Superficial / Fraco. O texto aborda o Moodle apenas de forma vaga ou genérica.")
        feedback_lines.append("- **Ponto de Melhoria:** Não foram explicados os conceitos de aprendizagem ativa e colaborativa nem foram citadas ferramentas práticas do ambiente.")

    feedback_text = "\n".join(feedback_lines)

    return {
        "marks": computed_marks,
        "feedback": feedback_text,
        "laya_raw": answers
    }


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True


class LayaRequestHandler(BaseHTTPRequestHandler):
    def _send_json(self, status_code: int, data: dict):
        response_bytes = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(response_bytes)))
        self.end_headers()
        self.wfile.write(response_bytes)

    def _check_auth(self) -> bool:
        if not API_KEY:
            return True
        auth_header = self.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:].strip()
            if token == API_KEY:
                return True
        return False

    def do_GET(self):
        if self.path in ("/health", "/healthz"):
            self._send_json(200, {
                "status": "healthy",
                "service": "laya-decision-engine",
                "model": "convaiinnovations/laya"
            })
        else:
            self._send_json(404, {"error": "Not Found"})

    def do_POST(self):
        if not self._check_auth():
            self._send_json(401, {"error": "Unauthorized: Invalid or missing Bearer token"})
            return

        content_length = int(self.headers.get("Content-Length", 0))
        if content_length <= 0:
            self._send_json(400, {"error": "Empty body"})
            return

        try:
            body = self.rfile.read(content_length).decode("utf-8")
            payload = json.loads(body)
        except Exception as e:
            self._send_json(400, {"error": f"Invalid JSON payload: {e}"})
            return

        # Route: Native System 1 /v1/systemone
        if self.path == "/v1/systemone":
            state = payload.get("state")
            questions = payload.get("questions")
            if not state or not questions:
                self._send_json(400, {"error": "Missing 'state' or 'questions'"})
                return
            try:
                res = agent.predict(state, questions)
                self._send_json(200, res)
            except Exception as e:
                logger.error(f"Prediction error: {e}", exc_info=True)
                self._send_json(500, {"error": str(e)})

        # Route: Direct Moodle Grading /v1/grade
        elif self.path in ("/v1/grade", "/grade"):
            response_text = payload.get("response", "")
            question_text = payload.get("questiontext", "")
            aiprompt = payload.get("aiprompt", "")
            markscheme = payload.get("markscheme", "")
            defaultmark = float(payload.get("defaultmark", 100.0))

            # If prompt was sent as a whole block, parse out the student response
            if not response_text and payload.get("prompt"):
                full_prompt = payload["prompt"]
                if "=== STUDENT RESPONSE TO GRADE ===" in full_prompt:
                    parts = full_prompt.split("=== STUDENT RESPONSE TO GRADE ===")
                    after = parts[1]
                    if "===" in after:
                        response_text = after.split("===")[0].strip()
                    else:
                        response_text = after.strip()
                else:
                    response_text = full_prompt

            try:
                grading = evaluate_student_response(response_text, question_text, aiprompt, markscheme, defaultmark)
                self._send_json(200, grading)
            except Exception as e:
                logger.error(f"Grading error: {e}", exc_info=True)
                self._send_json(500, {"error": str(e)})

        # Route: OpenAI compatible /v1/chat/completions
        elif self.path in ("/v1/chat/completions", "/chat/completions"):
            messages = payload.get("messages", [])
            prompt_combined = ""
            for msg in messages:
                prompt_combined += f"\n{msg.get('content', '')}"

            # Extract student response if delimited or parse whole prompt
            response_text = prompt_combined
            grading = evaluate_student_response(response_text, defaultmark=100.0)

            # Return JSON format expected by Moodle aitext: {"feedback": "...", "marks": X}
            content_json = json.dumps({
                "feedback": grading["feedback"],
                "marks": grading["marks"]
            }, ensure_ascii=False)

            openai_response = {
                "id": "chatcmpl-laya-local",
                "object": "chat.completion",
                "created": 1762200000,
                "model": "laya-system1",
                "choices": [{
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": content_json
                    },
                    "finish_reason": "stop"
                }],
                "usage": {
                    "prompt_tokens": 100,
                    "completion_tokens": 50,
                    "total_tokens": 150
                }
            }
            self._send_json(200, openai_response)

        else:
            self._send_json(404, {"error": f"Endpoint not found: {self.path}"})

    def log_message(self, format, *args):
        logger.info(f"{self.address_string()} - {format % args}")


def run():
    port = int(os.environ.get("LAYA_PORT", "8000"))
    server_address = ("0.0.0.0", port)
    httpd = ThreadedHTTPServer(server_address, LayaRequestHandler)
    logger.info(f"🚀 Laya HTTP Server running on http://0.0.0.0:{port}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    logger.info("Server stopped.")


if __name__ == "__main__":
    run()
