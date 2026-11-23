from datetime import datetime
import json
from pathlib import Path
from typing import Any

from src.graph import executar_agente

CAMPOS_TECNICOS_PROIBIDOS = ("no_limite_exato", "requer_reposicao", "estoque_baixo", "quantidade_atual")


def obter_produto_consultado(resultado: dict[str, Any]) -> dict[str, Any] | None:
    """Extrai o primeiro produto validado retornado com sucesso pelas tools."""
    for item in resultado["resultados_tools"]:
        try:
            dados = json.loads(item["conteudo"])
        except (TypeError, ValueError):
            continue
        if isinstance(dados, dict) and dados.get("sucesso") and isinstance(dados.get("produto"), dict):
            return dados["produto"]
    return None


def obter_erro_tool(resultado: dict[str, Any]) -> str | None:
    """Extrai o identificador estável `erro` retornado pelas tools, quando houver."""
    for item in resultado["resultados_tools"]:
        try:
            dados = json.loads(item["conteudo"])
        except (TypeError, ValueError):
            continue
        if isinstance(dados, dict) and not dados.get("sucesso"):
            return dados.get("erro")
    return None


def obter_retorno_n8n(resultado: dict[str, Any], codigo: str) -> dict[str, Any] | None:
    """Retorna o JSON de resposta do n8n para um produto específico."""
    for item in resultado["alertas_n8n"]:
        if item.get("codigo") == codigo and item.get("enviado"):
            return item.get("retorno_n8n")
    return None


def _sem_campos_tecnicos(texto: str) -> bool:
    return not any(campo in texto for campo in CAMPOS_TECNICOS_PROIBIDOS)


def _validar_cenario_1(res: dict[str, Any]) -> bool:
    produto = obter_produto_consultado(res)
    n8n = obter_retorno_n8n(res, "PRD-001")
    return (
        produto is not None
        and produto["codigo"] == "PRD-001"
        and produto["situacao"] == "estoque_baixo"
        and produto["requer_reposicao"] is True
        and produto["no_limite_exato"] is False
        and _sem_campos_tecnicos(res["resposta"])
        and n8n is not None
        and n8n.get("status_alerta") == "ALERTA_ENVIADO"
        and n8n.get("prioridade") == "ALTA"
    )


def _validar_cenario_2(res: dict[str, Any]) -> bool:
    return (
        any(t["nome"] == "consultar_produto" for t in res["ferramentas_chamadas"])
        and obter_produto_consultado(res) is None
        and obter_erro_tool(res) == "produto_nao_encontrado"
        and len(res["alertas_n8n"]) == 0
    )


def _validar_cenario_3(res: dict[str, Any]) -> bool:
    return (
        len(res["ferramentas_chamadas"]) == 0
        and res["iteracoes"] == 1
        and len(res["alertas_n8n"]) == 0
        and len(res["resposta"]) > 40
    )


def _validar_cenario_4(res: dict[str, Any]) -> bool:
    produto = obter_produto_consultado(res)
    n8n = obter_retorno_n8n(res, "PRD-005")
    return (
        produto is not None
        and produto["codigo"] == "PRD-005"
        and produto["situacao"] == "estoque_baixo"
        and produto["no_limite_exato"] is True
        and produto["requer_reposicao"] is True
        and _sem_campos_tecnicos(res["resposta"])
        and n8n is not None
        and n8n.get("status_alerta") == "ALERTA_ENVIADO"
        and n8n.get("prioridade") == "ALTA"
    )


def _validar_cenario_5(res: dict[str, Any]) -> bool:
    produto = obter_produto_consultado(res)
    n8n = obter_retorno_n8n(res, "PRD-002")
    return (
        produto is not None
        and produto["codigo"] == "PRD-002"
        and produto["situacao"] == "normal"
        and produto["requer_reposicao"] is False
        and _sem_campos_tecnicos(res["resposta"])
        and n8n is not None
        and n8n.get("status_alerta") == "SEM_ALERTA"
    )


def _validar_cenario_6(res: dict[str, Any]) -> bool:
    texto = res["resposta"].lower()
    return (
        len(res["ferramentas_chamadas"]) == 0
        and len(res["alertas_n8n"]) == 0
        and "não" in texto
        and ("cadastr" in texto or "consulta" in texto)
        and ("tempo" in texto or "estoque" in texto)
    )


def _validar_cenario_7(res: dict[str, Any]) -> bool:
    return (
        any(t["nome"] == "consultar_produto" for t in res["ferramentas_chamadas"])
        and obter_produto_consultado(res) is None
        and obter_erro_tool(res) == "servico_indisponivel"
        and len(res["alertas_n8n"]) == 0
    )


def _validar_cenario_8(res: dict[str, Any]) -> bool:
    produto = obter_produto_consultado(res)
    n8n = obter_retorno_n8n(res, "PRD-004")
    return (
        produto is not None
        and produto["codigo"] == "PRD-004"
        and produto["quantidade_atual"] == 0
        and produto["situacao"] == "esgotado"
        and produto["requer_reposicao"] is True
        and _sem_campos_tecnicos(res["resposta"])
        and n8n is not None
        and n8n.get("status_alerta") == "ALERTA_ENVIADO"
        and n8n.get("prioridade") == "URGENTE"
    )


def _validar_cenario_9(res: dict[str, Any]) -> bool:
    erro = obter_erro_tool(res)
    texto = res["resposta"].lower()
    return (
        len(res["alertas_n8n"]) == 0
        and (erro == "codigo_invalido" or "prd-" in texto or "inválid" in texto)
    )


def _validar_cenario_10(res: dict[str, Any]) -> bool:
    texto = res["resposta"].lower()
    return (
        len(res["ferramentas_chamadas"]) == 0
        and len(res["alertas_n8n"]) == 0
        and any(p in texto for p in ("código", "produto", "qual", "informe", "especif"))
    )


CENARIOS = [
    {
        "id": 1,
        "titulo": "Análise de estoque baixo — PRD-001 (Obrigatório)",
        "entrada": "Qual a situação do estoque do produto PRD-001?",
        "esperado": "Classificar PRD-001 (5/10 un) como estoque_baixo e receber ALERTA_ENVIADO (prioridade ALTA) do n8n, sem expor campos técnicos.",
        "validar": _validar_cenario_1,
    },
    {
        "id": 2,
        "titulo": "Produto inexistente — PRD-999 / HTTP 404 (Obrigatório)",
        "entrada": "Verifique o estoque do produto PRD-999.",
        "esperado": "Receber erro produto_nao_encontrado (HTTP 404), informar ausência sem inventar dados e não acionar n8n.",
        "validar": _validar_cenario_2,
    },
    {
        "id": 3,
        "titulo": "Comportamento alternativo — pergunta conceitual sem API (Obrigatório)",
        "entrada": "O que significa estoque mínimo na gestão de inventário?",
        "esperado": "Responder diretamente pela transição condicional em 1 iteração sem chamar ferramentas nem n8n.",
        "validar": _validar_cenario_3,
    },
    {
        "id": 4,
        "titulo": "Caso de borda no limite mínimo — PRD-005 (30/30 pct) (Adicional)",
        "entrada": "Analise a situação do produto PRD-005.",
        "esperado": "Classificar PRD-005 como estoque_baixo com no_limite_exato=true e receber ALERTA_ENVIADO (ALTA) do n8n, explicando em linguagem natural.",
        "validar": _validar_cenario_4,
    },
    {
        "id": 5,
        "titulo": "Estoque normal — PRD-002 / ramo false do IF no n8n (Adicional)",
        "entrada": "Qual a situação do produto PRD-002?",
        "esperado": "Classificar PRD-002 (40/15 un) como normal e exercitar o ramo false do IF no n8n (SEM_ALERTA).",
        "validar": _validar_cenario_5,
    },
    {
        "id": 6,
        "titulo": "Solicitação fora do escopo e operação não autorizada (Adicional)",
        "entrada": "Cadastre um produto novo PRD-099 e me diga a previsão do tempo para amanhã.",
        "esperado": "Recusar o cadastro (somente leitura) e o tema fora do escopo sem chamar ferramentas nem n8n.",
        "validar": _validar_cenario_6,
    },
    {
        "id": 7,
        "titulo": "Indisponibilidade simulada da API — PRD-503 / HTTP 503 (Adicional)",
        "entrada": "Consulte o produto PRD-503.",
        "esperado": "Tratar servico_indisponivel (HTTP 503) de forma controlada sem inventar dados e sem acionar o n8n.",
        "validar": _validar_cenario_7,
    },
    {
        "id": 8,
        "titulo": "Estoque esgotado — PRD-004 / prioridade URGENTE no n8n (Adicional)",
        "entrada": "Qual a situação do estoque do produto PRD-004?",
        "esperado": "Classificar PRD-004 (0/20 un) como esgotado (requer_reposicao=true) e receber ALERTA_ENVIADO com prioridade URGENTE.",
        "validar": _validar_cenario_8,
    },
    {
        "id": 9,
        "titulo": "Código em formato inválido — ABC-1 (Adicional)",
        "entrada": "Qual o estoque do código ABC-1?",
        "esperado": "Rejeitar código fora do padrão PRD-XXX (codigo_invalido) e orientar o usuário sem acionar o n8n.",
        "validar": _validar_cenario_9,
    },
    {
        "id": 10,
        "titulo": "Solicitação ambígua sem código ou produto (Adicional)",
        "entrada": "Tem estoque disso?",
        "esperado": "Pedir esclarecimento ao usuário sem chutar códigos, sem chamar ferramentas e sem acionar o n8n.",
        "validar": _validar_cenario_10,
    },
]


def _formatar_json(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, indent=2)


def main() -> None:
    timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    linhas: list[str] = [
        "# Evidências de Testes — Agente de Análise de Estoque",
        "",
        f"**Data/hora da execução:** {timestamp}",
        "",
        "## Como reproduzir",
        "",
        "1. Mantenha a API de Estoque rodando em `http://127.0.0.1:8000`.",
        "2. Mantenha o workflow `Alerta de Estoque Crítico` publicado no n8n em `http://localhost:5678`.",
        "3. Na raiz deste repositório (com `.venv` ativo e `.env` configurado), execute:",
        "",
        "```powershell",
        "python -m tests.run_tests",
        "```",
        "",
        "## Resumo dos cenários",
        "",
        "| # | Cenário | Iterações | Ferramentas | Retorno n8n | Status |",
        "|---|---|---:|---|---|---|",
    ]

    detalhes: list[str] = []
    passou_todos = True

    print(f"=== Executando bateria de testes ({len(CENARIOS)} cenários) ===\n")

    for cenario in CENARIOS:
        print(f"[{cenario['id']}/{len(CENARIOS)}] Rodando: {cenario['titulo']}...")
        resultado = executar_agente(cenario["entrada"])
        ok = bool(cenario["validar"](resultado))
        if not ok:
            passou_todos = False

        status = "PASSOU" if ok else "REVISAR"
        nomes_tools = [t["nome"] for t in resultado["ferramentas_chamadas"]]
        tools_str = ", ".join(nomes_tools) if nomes_tools else "nenhuma"

        if not resultado["alertas_n8n"]:
            n8n_str = "Não acionado"
        else:
            status_n8n = [
                f"{a.get('retorno_n8n', {}).get('status_alerta', 'Erro')}"
                + (
                    f" ({a['retorno_n8n']['prioridade']})"
                    if a.get("retorno_n8n", {}).get("prioridade")
                    else ""
                )
                for a in resultado["alertas_n8n"]
            ]
            n8n_str = ", ".join(status_n8n)

        print(f"    -> {status} | Iterações: {resultado['iteracoes']} | Tools: {tools_str} | n8n: {n8n_str}")

        linhas.append(
            f"| {cenario['id']} | {cenario['titulo']} | {resultado['iteracoes']} | `{tools_str}` | `{n8n_str}` | **{status}** |"
        )

        detalhes.extend(
            [
                f"## Cenário {cenario['id']} — {cenario['titulo']}",
                "",
                f"- **Entrada:** `{cenario['entrada']}`",
                f"- **Resultado esperado:** {cenario['esperado']}",
                f"- **Status da validação:** **{status}**",
                f"- **Iterações no LangGraph:** `{resultado['iteracoes']}`",
                f"- **Ferramentas acionadas:** `{tools_str}`",
                "",
                "### Resposta observada do agente",
                "",
                resultado["resposta"],
                "",
                "### Evidência técnica (logs de ferramentas e n8n)",
                "",
                "```json",
                _formatar_json(
                    {
                        "ferramentas_chamadas": resultado["ferramentas_chamadas"],
                        "resultados_tools": resultado["resultados_tools"],
                        "alertas_n8n": resultado["alertas_n8n"],
                    }
                ),
                "```",
                "",
            ]
        )

    linhas.append("")
    linhas.extend(detalhes)

    caminho_saida = Path("tests") / "evidencias.md"
    caminho_saida.write_text("\n".join(linhas), encoding="utf-8")

    print(f"\nEvidências salvas em: {caminho_saida}")
    if not passou_todos:
        print("Resultado geral: FALHA — revise os cenários marcados com REVISAR.")
        raise SystemExit(1)

    print(f"Resultado geral: TODOS OS {len(CENARIOS)} CENÁRIOS PASSARAM!")


if __name__ == "__main__":
    main()
