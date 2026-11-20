import os
from dotenv import load_dotenv

load_dotenv()

GOOGLE_API_KEY=os.getenv("GOOGLE_API_KEY").strip()
GEMINI_MODEL=os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip()
API_ESTOQUE_URL=os.getenv("API_ESTOQUE_URL", "http://127.0.0.1:8000").rstrip("/")
N8N_WEBHOOK_URL=os.getenv("N8N_WEBHOOK_URL","").strip()

def validar_configuracao() -> None:
    """ Garante que a chave do LLM foi carregada voa .env antes de iniciar o agente. """
    if not GOOGLE_API_KEY:
        raise RuntimeError(
            "GOOGLE_API_KEY não configurada. Copie .env.example para .env e informe sua chave.")