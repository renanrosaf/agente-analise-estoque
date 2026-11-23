import re
from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from src.config import API_ESTOQUE_URL

PADRAO_CODIGO = re.compile(r"^PRD-[0-9]{3}$")
TIMEOUT_SEGUNDOS = 5.0


class ProdutoAPI(BaseModel):
    """Contrato estrito de um produto retornado pela API de Estoque."""

    model_config = ConfigDict(strict=True)

    codigo: str = Field(pattern=r"^PRD-[0-9]{3}$")
    nome: str = Field(min_length=1)
    categoria: str = Field(min_length=1)
    quantidade_atual: int = Field(ge=0)
    estoque_minimo: int = Field(ge=0)
    unidade: str = Field(min_length=1)


def classificar_produto(dados_brutos: dict[str, Any]) -> dict[str, Any]:
    """Valida os dados com Pydantic (strict=True) e calcula a classificação oficial de estoque.

    Args:
        dados_brutos: Dicionário JSON retornado pela API de Estoque.

    Returns:
        Dicionário do produto validado acrescido de `situacao`, `no_limite_exato` e `requer_reposicao`.
    """
    produto = ProdutoAPI.model_validate(dados_brutos)

    if produto.quantidade_atual == 0:
        situacao = "esgotado"
        requer_reposicao = True
        no_limite_exato = False
    elif produto.quantidade_atual <= produto.estoque_minimo:
        situacao = "estoque_baixo"
        requer_reposicao = True
        no_limite_exato = produto.quantidade_atual == produto.estoque_minimo
    else:
        situacao = "normal"
        requer_reposicao = False
        no_limite_exato = False

    return {
        **produto.model_dump(),
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
    """Consulta um produto específico na API de Estoque pelo código.

    Args:
        codigo: Código do produto no formato PRD-XXX (três dígitos, ex.: 'PRD-001').

    Returns:
        Dicionário com `sucesso=True` e os dados validados/classificados em `produto`,
        ou `sucesso=False` com `erro` e `mensagem` em caso de falha ou código inválido.
    """
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
            "mensagem": f"A API de estoque em {API_ESTOQUE_URL} demorou demais para responder. Tente novamente.",
        }
    except httpx.ConnectError:
        return {
            "sucesso": False,
            "erro": "api_indisponivel",
            "mensagem": f"Não foi possível conectar à API de estoque em {API_ESTOQUE_URL}. Verifique se o serviço está ativo.",
        }
    except httpx.HTTPError as exc:
        return {
            "sucesso": False,
            "erro": "erro_http",
            "mensagem": f"Falha de comunicação HTTP com a API de estoque ({API_ESTOQUE_URL}): {exc}",
        }

    dados = _ler_json_seguro(resposta)

    if resposta.status_code == 200:
        try:
            produto_validado = classificar_produto(dados)
        except ValidationError as exc:
            return {
                "sucesso": False,
                "erro": "dados_api_invalidos",
                "mensagem": f"Resposta da API fora do contrato esperado: {exc.error_count()} erro(s) de validação.",
            }
        return {"sucesso": True, "produto": produto_validado}

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
    """Lista os produtos do estoque com resumo consolidado por situação.

    Args:
        categoria: Nome opcional da categoria para filtrar (ex.: 'Periféricos', 'Papelaria').

    Returns:
        Dicionário com `sucesso=True`, `total`, `resumo` (contagens por situação) e `produtos`
        validados/classificados, ou `sucesso=False` com `erro` e `mensagem`.
    """
    params = {"categoria": categoria.strip()} if categoria and categoria.strip() else None

    try:
        resposta = httpx.get(
            f"{API_ESTOQUE_URL}/produtos",
            params=params,
            timeout=TIMEOUT_SEGUNDOS,
        )
    except httpx.HTTPError as exc:
        return {
            "sucesso": False,
            "erro": "erro_http",
            "mensagem": f"Não foi possível consultar a lista de produtos em {API_ESTOQUE_URL}: {exc}",
        }

    if resposta.status_code != 200:
        return {
            "sucesso": False,
            "erro": f"http_{resposta.status_code}",
            "mensagem": f"Falha ao listar produtos (HTTP {resposta.status_code}).",
        }

    dados = _ler_json_seguro(resposta)
    try:
        produtos_classificados = [classificar_produto(p) for p in dados.get("produtos", [])]
    except ValidationError as exc:
        return {
            "sucesso": False,
            "erro": "dados_api_invalidos",
            "mensagem": f"Lista de produtos da API fora do contrato esperado: {exc.error_count()} erro(s).",
        }

    resumo = {
        "esgotado": sum(1 for p in produtos_classificados if p["situacao"] == "esgotado"),
        "estoque_baixo": sum(1 for p in produtos_classificados if p["situacao"] == "estoque_baixo"),
        "no_limite_exato": sum(1 for p in produtos_classificados if p["no_limite_exato"]),
        "normal": sum(1 for p in produtos_classificados if p["situacao"] == "normal"),
        "requerem_reposicao": sum(1 for p in produtos_classificados if p["requer_reposicao"]),
    }

    return {
        "sucesso": True,
        "total": dados.get("total", len(produtos_classificados)),
        "resumo": resumo,
        "produtos": produtos_classificados,
    }


@tool
def listar_categorias() -> dict[str, Any]:
    """Lista todas as categorias disponíveis na API de Estoque.

    Returns:
        Dicionário com `sucesso=True`, `total` e `categorias`, ou `sucesso=False` com `erro` e `mensagem`.
    """
    try:
        resposta = httpx.get(f"{API_ESTOQUE_URL}/categorias", timeout=TIMEOUT_SEGUNDOS)
    except httpx.HTTPError as exc:
        return {
            "sucesso": False,
            "erro": "erro_http",
            "mensagem": f"Não foi possível consultar as categorias em {API_ESTOQUE_URL}: {exc}",
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