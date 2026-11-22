import os
from dotenv import load_dotenv

load_dotenv()

PLACEHOLDERS_INVALIDOS = {
    "",
    "sua_chave_groq_aqui",
    "cole_sua_chave_aqui",
    "sua_chave_aqui",
}

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b").strip()
API_ESTOQUE_URL = os.getenv("API_ESTOQUE_URL", "http://127.0.0.1:8000").rstrip("/")
N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL", "").strip()


def validar_configuracao() -> None:
    """Garante que uma chave real do LLM foi configurada antes de iniciar o agente."""
    if GROQ_API_KEY.lower() in PLACEHOLDERS_INVALIDOS:
        raise RuntimeError(
            "GROQ_API_KEY não configurada ou ainda está com valor de exemplo. "
            "Informe uma chave válida no arquivo .env ou nas variáveis de ambiente."
        )