import re
from typing import Any

import httpx
from langchain_core.tools import tool

from src.config import API_ESTOQUE_URL

PADRAO_CODIGO = re.compile(r"^PRD-[0-9]{3}$")
TIMEOUT_SEGUNDOS = 5.0


def classificar_produto(produto: dict[str, Any]) -> dict[str, Any]:
    """Fonte única de verdade para classificação de estoque (inclui limite mínimo em estoque_baixo)."""
    qtd = int(produto["quantidade_atual"])
    minimo = int(produto["estoque_minimo"])

    if qtd == 0:
        situacao = "esgotado"
        requer_reposicao = True
        no_limite_exato = False
    elif qtd <= minimo:
        situacao = "estoque_baixo"
        requer_reposicao = True
        no_limite_exato = qtd == minimo
    else:
        situacao = "normal"
        requer_reposicao = False
        no_limite_exato = False

    return {
        **produto,
        "situacao": situacao,
        "no_limite_exato": no_limite_exato,
        "requer_reposicao": requer_reposicao,
    }


def _ler_json_seguro(resposta: httpx.Response) -> dict[str, Any]:
    try:
        return resposta.json()
    except ValueError:
        return {}


@tool
def consultar_produto(codigo: str) -> dict[str, Any]:
    """Consulta um produto específico na API de Estoque pelo código no formato PRD-XXX (ex.: PRD-001)."""
    codigo_limpo = codigo.strip().upper()
    if not PADRAO_CODIGO.match(codigo_limpo):
        return {
            "sucesso": False,
            "erro": "codigo_invalido",
            "mensagem": (
                f"Código '{codigo}' inválido. Informe no padrão PRD-XXX "
                "(três dígitos, exemplo: PRD-001)."
            ),
        }

    try:
        resposta = httpx.get(
            f"{API_ESTOQUE_URL}/produtos/{codigo_limpo}",
            timeout=TIMEOUT_SEGUNDOS,
        )
    except httpx.TimeoutException:
        return {
            "sucesso": False,
            "erro": "timeout_api",
            "mensagem": "A API de estoque demorou demais para responder. Tente novamente.",
        }
    except httpx.ConnectError:
        return {
            "sucesso": False,
            "erro": "api_indisponivel",
            "mensagem": "Não foi possível conectar à API de estoque. Verifique se ela está rodando em 127.0.0.1:8000.",
        }

    dados = _ler_json_seguro(resposta)

    if resposta.status_code == 200:
        return {"sucesso": True, "produto": classificar_produto(dados)}

    if resposta.status_code == 404:
        return {
            "sucesso": False,
            "erro": dados.get("erro", "produto_nao_encontrado"),
            "mensagem": f"Produto {codigo_limpo} não encontrado na base de estoque.",
        }

    if resposta.status_code == 503:
        return {
            "sucesso": False,
            "erro": dados.get("erro", "servico_indisponivel"),
            "mensagem": dados.get(
                "mensagem",
                "Serviço temporariamente indisponível. Tente novamente mais tarde.",
            ),
        }

    return {
        "sucesso": False,
        "erro": dados.get("erro", f"http_{resposta.status_code}"),
        "mensagem": dados.get("mensagem", f"Erro inesperado da API (HTTP {resposta.status_code})."),
    }


@tool
def listar_produtos(categoria: str | None = None) -> dict[str, Any]:
    """Lista todos os produtos do estoque. Opcionalmente filtra por categoria (ex.: 'Periféricos', 'Papelaria')."""
    params = {"categoria": categoria.strip()} if categoria and categoria.strip() else None

    try:
        resposta = httpx.get(
            f"{API_ESTOQUE_URL}/produtos",
            params=params,
            timeout=TIMEOUT_SEGUNDOS,
        )
    except (httpx.ConnectError, httpx.TimeoutException):
        return {
            "sucesso": False,
            "erro": "api_indisponivel",
            "mensagem": "Não foi possível consultar a lista de produtos na API de estoque.",
        }

    if resposta.status_code != 200:
        return {
            "sucesso": False,
            "erro": f"http_{resposta.status_code}",
            "mensagem": f"Falha ao listar produtos (HTTP {resposta.status_code}).",
        }

    dados = _ler_json_seguro(resposta)
    produtos_classificados = [classificar_produto(p) for p in dados.get("produtos", [])]
    return {
        "sucesso": True,
        "total": dados.get("total", len(produtos_classificados)),
        "produtos": produtos_classificados,
    }


@tool
def listar_categorias() -> dict[str, Any]:
    """Lista todas as categorias disponíveis na API de Estoque (útil antes de filtrar por categoria)."""
    try:
        resposta = httpx.get(f"{API_ESTOQUE_URL}/categorias", timeout=TIMEOUT_SEGUNDOS)
    except (httpx.ConnectError, httpx.TimeoutException):
        return {
            "sucesso": False,
            "erro": "api_indisponivel",
            "mensagem": "Não foi possível consultar as categorias na API de estoque.",
        }

    if resposta.status_code != 200:
        return {
            "sucesso": False,
            "erro": f"http_{resposta.status_code}",
            "mensagem": f"Falha ao listar categorias (HTTP {resposta.status_code}).",
        }

    dados = _ler_json_seguro(resposta)
    return {
        "sucesso": True,
        "total": dados.get("total", 0),
        "categorias": dados.get("categorias", []),
    }


TOOLS = [consultar_produto, listar_produtos, listar_categorias]