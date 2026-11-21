import os
from dotenv import load_dotenv

load_dotenv(override=True)  # Carrega variáveis de ambiente do arquivo .env, se existir

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b").strip()
API_ESTOQUE_URL = os.getenv("API_ESTOQUE_URL", "http://127.0.0.1:8000").rstrip("/")
N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL", "").strip()


def validar_configuracao() -> None:
    """Garante que a chave do LLM foi carregada via .env antes de iniciar o agente."""
    if not GROQ_API_KEY:
        raise RuntimeError(
            "GROQ_API_KEY não configurada. Copie .env.example para .env e informe sua chave."
        )