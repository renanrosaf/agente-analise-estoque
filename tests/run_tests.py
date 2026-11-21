from datetime import datetime
import json
from pathlib import Path
from typing import Any

from src.graph import executar_agente
from src.n8n_client import notificar_produtos_criticos

CENARIOS = [
    {
        "id": 1,
        "titulo": "Análise de estoque de produto existente (Obrigatório)",
        "entrada": "Qual a situação do estoque do produto PRD-001?",
        "esperado": (
            "Chamar a ferramenta consultar_produto com PRD-001, identificar 5 un disponíveis "
            "frente ao estoque mínimo de 10 un, classificar como estoque baixo, recomendar reposição "
            "e acionar o alerta no webhook do n8n."
        ),
        "validar": lambda res, alertas: (
            any(t["nome"] == "consultar_produto" for t in res["ferramentas_chamadas"])
            and "PRD-001" in res["resposta"]
            and "baixo" in res["resposta"].lower()
            and any(a.get("enviado") for a in alertas)
        ),
    },
    {
        "id": 2,
        "titulo": "Consulta de produto inexistente — HTTP 404 (Obrigatório)",
        "entrada": "Verifique o estoque do produto PRD-999.",
        "esperado": (
            "Chamar consultar_produto com PRD-999, receber erro 404 (produto_nao_encontrado) "
            "e informar a ausência do produto sem inventar quantidades."
        ),
        "validar": lambda res, alertas: (
            any(t["nome"] == "consultar_produto" for t in res["ferramentas_chamadas"])
            and any("produto_nao_encontrado" in r["conteudo"] for r in res["resultados_tools"])
            and len(alertas) == 0
        ),
    },
    {
        "id": 3,
        "titulo": "Comportamento alternativo — pergunta conceitual sem chamar API (Obrigatório)",
        "entrada": "O que significa estoque mínimo na gestão de inventário?",
        "esperado": (
            "Responder diretamente pela transição condicional do LangGraph SEM chamar nenhuma "
            "ferramenta nem consultar a API (ferramentas_chamadas == [])."
        ),
        "validar": lambda res, alertas: (
            len(res["ferramentas_chamadas"]) == 0
            and res["iteracoes"] == 1
            and len(res["resposta"].strip()) > 40
        ),
    },
    {
        "id": 4,
        "titulo": "Indisponibilidade simulada da API — HTTP 503 (Bônus de confiabilidade)",
        "entrada": "Consulte o produto PRD-503.",
        "esperado": (
            "Chamar consultar_produto com PRD-503, tratar o erro HTTP 503 (servico_indisponivel) "
            "e avisar o usuário de forma controlada sem inventar dados."
        ),
        "validar": lambda res, alertas: (
            any(t["nome"] == "consultar_produto" for t in res["ferramentas_chamadas"])
            and any("servico_indisponivel" in r["conteudo"] for r in res["resultados_tools"])
        ),
    },
    {
        "id": 5,
        "titulo": "Validação de código em formato inválido — ABC-1 (Bônus de segurança)",
        "entrada": "Qual o estoque do código ABC-1?",
        "esperado": (
            "Rejeitar o parâmetro fora do padrão PRD-XXX (validação local na tool ou orientação "
            "direta do agente) e orientar o usuário sobre o formato correto sem inventar dados."
        ),
        "validar": lambda res, alertas: (
            "PRD-" in res["resposta"] or "inválid" in res["resposta"].lower()
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
        "| # | Cenário | Iterações | Ferramentas | n8n | Status |",
        "|---|---|---:|---|---|---|",
    ]

    detalhes: list[str] = []
    passou_todos = True

    print("=== Executando bateria de testes do Agente de Estoque ===\n")

    for cenario in CENARIOS:
        print(f"[{cenario['id']}/{len(CENARIOS)}] Rodando: {cenario['titulo']}...")
        resultado = executar_agente(cenario["entrada"])
        alertas = notificar_produtos_criticos(resultado["resultados_tools"])
        ok = bool(cenario["validar"](resultado, alertas))
        if not ok:
            passou_todos = False

        status = "PASSOU" if ok else "REVISAR"
        nomes_tools = [t["nome"] for t in resultado["ferramentas_chamadas"]]
        tools_str = ", ".join(nomes_tools) if nomes_tools else "nenhuma"
        n8n_str = "Alerta enviado" if any(a.get("enviado") for a in alertas) else "Não acionado"

        print(f"    -> {status} | Iterações: {resultado['iteracoes']} | Tools: {tools_str} | n8n: {n8n_str}")

        linhas.append(
            f"| {cenario['id']} | {cenario['titulo']} | {resultado['iteracoes']} | `{tools_str}` | {n8n_str} | **{status}** |"
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
                        "alertas_n8n": alertas,
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
    print("Resultado geral:", "TODOS OS CENÁRIOS PASSARAM!" if passou_todos else "Algum cenário precisa de revisão.")


if __name__ == "__main__":
    main()