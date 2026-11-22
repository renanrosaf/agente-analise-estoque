import json
from typing import Any

import httpx

from src.config import N8N_WEBHOOK_URL

TIMEOUT_N8N = 5.0


def enviar_produto_n8n(produto: dict[str, Any]) -> dict[str, Any]:
    """Envia os dados já classificados de um produto ao Webhook do n8n para decisão no nó IF."""
    if not N8N_WEBHOOK_URL:
        return {
            "codigo": produto.get("codigo"),
            "enviado": False,
            "mensagem": "N8N_WEBHOOK_URL não configurada.",
        }

    try:
        resposta = httpx.post(N8N_WEBHOOK_URL, json=produto, timeout=TIMEOUT_N8N)
        resposta.raise_for_status()
        return {
            "codigo": produto.get("codigo"),
            "situacao": produto.get("situacao"),
            "enviado": True,
            "status_http": resposta.status_code,
            "retorno_n8n": resposta.json(),
        }
    except Exception as exc:
        return {
            "codigo": produto.get("codigo"),
            "situacao": produto.get("situacao"),
            "enviado": False,
            "mensagem": f"Falha ao acionar n8n: {exc}",
        }


def extrair_produtos_das_mensagens(mensagens: list[Any]) -> list[dict[str, Any]]:
    """Extrai produtos únicos retornados pelas ToolMessages do estado do LangGraph."""
    produtos_unicos: dict[str, dict[str, Any]] = {}

    for msg in mensagens:
        conteudo = getattr(msg, "content", None)
        if not isinstance(conteudo, str):
            continue
        try:
            dados = json.loads(conteudo)
        except ValueError:
            continue

        if not isinstance(dados, dict) or not dados.get("sucesso"):
            continue

        if "produto" in dados and isinstance(dados["produto"], dict):
            p = dados["produto"]
            if "codigo" in p:
                produtos_unicos[p["codigo"]] = p
        elif "produtos" in dados and isinstance(dados["produtos"], list):
            for p in dados["produtos"]:
                if isinstance(p, dict) and "codigo" in p:
                    produtos_unicos[p["codigo"]] = p

    return list(produtos_unicos.values())


def processar_notificacoes_n8n(mensagens: list[Any]) -> list[dict[str, Any]]:
    """Envia todos os produtos analisados ao n8n, delegando ao workflow IF a decisão do alerta."""
    produtos = extrair_produtos_das_mensagens(mensagens)
    return [enviar_produto_n8n(produto) for produto in produtos]