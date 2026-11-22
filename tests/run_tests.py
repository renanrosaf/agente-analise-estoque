from datetime import datetime
import json
from pathlib import Path
from typing import Any

from src.graph import executar_agente

CENARIOS = [
    {
        "id": 1,
        "titulo": "Análise de estoque baixo — PRD-001 (Obrigatório)",
        "entrada": "Qual a situação do estoque do produto PRD-001?",
        "esperado": (
            "Chamar consultar_produto(PRD-001), retornar situacao='estoque_baixo' (5 de 10 un) "
            "e o nó notificar_n8n receber ALERTA_ENVIADO do workflow."
        ),
        "validar": lambda res: (
            any(t["nome"] == "consultar_produto" for t in res["ferramentas_chamadas"])
            and "PRD-001" in res["resposta"]
            and any(
                a.get("enviado") and a.get("retorno_n8n", {}).get("status_alerta") == "ALERTA_ENVIADO"
                for a in res["alertas_n8n"]
            )
        ),
    },
    {
        "id": 2,
        "titulo": "Consulta de produto inexistente — PRD-999 / HTTP 404 (Obrigatório)",
        "entrada": "Verifique o estoque do produto PRD-999.",
        "esperado": (
            "Chamar consultar_produto(PRD-999), tratar HTTP 404 (produto_nao_encontrado) "
            "sem inventar dados e sem acionar o n8n."
        ),
        "validar": lambda res: (
            any(t["nome"] == "consultar_produto" for t in res["ferramentas_chamadas"])
            and any("produto_nao_encontrado" in r["conteudo"] for r in res["resultados_tools"])
            and len(res["alertas_n8n"]) == 0
        ),
    },
    {
        "id": 3,
        "titulo": "Comportamento alternativo — pergunta conceitual sem API (Obrigatório)",
        "entrada": "O que significa estoque mínimo na gestão de inventário?",
        "esperado": (
            "Responder diretamente pela transição condicional sem chamar ferramentas (iteracoes == 1) "
            "e sem acionar o n8n."
        ),
        "validar": lambda res: (
            len(res["ferramentas_chamadas"]) == 0
            and res["iteracoes"] == 1
            and len(res["alertas_n8n"]) == 0
            and len(res["resposta"]) > 40
        ),
    },
    {
        "id": 4,
        "titulo": "Caso de borda no limite mínimo — PRD-005 (30/30 pct) (Bônus)",
        "entrada": "Analise a situação do produto PRD-005.",
        "esperado": (
            "Classificar PRD-005 (30/30 pct) como estoque_baixo com no_limite_exato=true "
            "e disparar ALERTA_ENVIADO no n8n."
        ),
        "validar": lambda res: (
            any('"no_limite_exato": true' in r["conteudo"] for r in res["resultados_tools"])
            and any(
                a.get("enviado") and a.get("retorno_n8n", {}).get("status_alerta") == "ALERTA_ENVIADO"
                for a in res["alertas_n8n"]
            )
        ),
    },
    {
        "id": 5,
        "titulo": "Produto em estoque normal — PRD-002 / ramo false do IF no n8n (Bônus)",
        "entrada": "Qual a situação do produto PRD-002?",
        "esperado": (
            "Classificar PRD-002 (40/15 un) como normal, enviar ao n8n e exercitar o ramo false "
            "do nó IF retornando SEM_ALERTA."
        ),
        "validar": lambda res: (
            any(
                a.get("enviado") and a.get("retorno_n8n", {}).get("status_alerta") == "SEM_ALERTA"
                for a in res["alertas_n8n"]
            )
        ),
    },
    {
        "id": 6,
        "titulo": "Solicitação fora do escopo e operação não autorizada (Bônus)",
        "entrada": "Cadastre um produto novo PRD-099 e me diga a previsão do tempo para amanhã.",
        "esperado": (
            "Recusar o cadastro (somente leitura) e recusar o tema fora do escopo de estoque, "
            "sem chamar ferramentas."
        ),
        "validar": lambda res: (
            len(res["ferramentas_chamadas"]) == 0
            and len(res["alertas_n8n"]) == 0
            and len(res["resposta"]) > 20
        ),
    },
    {
        "id": 7,
        "titulo": "Indisponibilidade simulada da API — PRD-503 / HTTP 503 (Bônus)",
        "entrada": "Consulte o produto PRD-503.",
        "esperado": (
            "Tratar HTTP 503 (servico_indisponivel) de forma controlada sem inventar dados."
        ),
        "validar": lambda res: (
            any(t["nome"] == "consultar_produto" for t in res["ferramentas_chamadas"])
            and any("servico_indisponivel" in r["conteudo"] for r in res["resultados_tools"])
        ),
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

    print("=== Executando bateria de testes (7 cenários) ===\n")

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
                a.get("retorno_n8n", {}).get("status_alerta", "Erro")
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
    print("Resultado geral:", "TODOS OS 7 CENÁRIOS PASSARAM!" if passou_todos else "Algum cenário precisa de revisão.")


if __name__ == "__main__":
    main()