import json
from typing import Any

import httpx

from src.config import N8N_WEBHOOK_URL

TIMEOUT_N8N = 5.0


def classificar_situacao(quantidade_atual: int, estoque_minimo: int) -> str:
    if quantidade_atual == 0:
        return "esgotado"
    if quantidade_atual < estoque_minimo:
        return "estoque_baixo"
    if quantidade_atual == estoque_minimo:
        return "no_limite"
    return "normal"


def enviar_alerta_n8n(produto: dict[str, Any]) -> dict[str, Any]:
    """Envia dados de um produto ao Webhook do n8n e retorna a resposta do workflow."""
    if not N8N_WEBHOOK_URL:
        return {"enviado": False, "mensagem": "N8N_WEBHOOK_URL não configurada."}

    situacao = classificar_situacao(
        int(produto["quantidade_atual"]),
        int(produto["estoque_minimo"]),
    )
    payload = {**produto, "situacao": situacao}

    try:
        resposta = httpx.post(N8N_WEBHOOK_URL, json=payload, timeout=TIMEOUT_N8N)
        resposta.raise_for_status()
        return {"enviado": True, "status_http": resposta.status_code, "retorno_n8n": resposta.json()}
    except Exception as exc:
        return {"enviado": False, "mensagem": f"Falha ao acionar n8n: {exc}"}


def notificar_produtos_criticos(resultados_tools: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Verifica resultados das tools e aciona o n8n para itens com estoque baixo ou esgotado."""
    produtos_avaliados: dict[str, dict[str, Any]] = {}

    for item in resultados_tools:
        try:
            dados = json.loads(item["conteudo"])
        except (TypeError, ValueError):
            continue
        if not isinstance(dados, dict) or not dados.get("sucesso"):
            continue

        if "produto" in dados and isinstance(dados["produto"], dict):
            p = dados["produto"]
            produtos_avaliados[p["codigo"]] = p
        elif "produtos" in dados and isinstance(dados["produtos"], list):
            for p in dados["produtos"]:
                if isinstance(p, dict) and "codigo" in p:
                    produtos_avaliados[p["codigo"]] = p

    alertas = []
    for produto in produtos_avaliados.values():
        situacao = classificar_situacao(
            int(produto["quantidade_atual"]),
            int(produto["estoque_minimo"]),
        )
        if situacao in {"esgotado", "estoque_baixo"}:
            alertas.append(enviar_alerta_n8n(produto))

    return alertas