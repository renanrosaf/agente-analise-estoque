from src.graph import executar_agente


def main() -> None:
    print("=== Agente de Análise de Estoque (LangGraph + Groq + n8n) ===")
    print("Digite sua pergunta ou 'sair' para encerrar.\n")

    while True:
        pergunta = input("Você: ").strip()
        if not pergunta:
            continue
        if pergunta.lower() in {"sair", "exit", "quit"}:
            print("Encerrando agente.")
            break

        try:
            resultado = executar_agente(pergunta)
        except Exception as exc:
            print(f"\n[Erro controlado] Não foi possível concluir a análise: {exc}\n")
            continue

        tools = [t["nome"] for t in resultado["ferramentas_chamadas"]]
        print(
            f"\n[Log] Iterações: {resultado['iteracoes']} "
            f"| Ferramentas usadas: {tools or 'nenhuma'} "
            f"| Limite atingido: {resultado.get('limite_atingido', False)}"
        )
        print(f"Agente:\n{resultado['resposta']}\n")

        for item in resultado["alertas_n8n"]:
            if item.get("enviado"):
                print(f"[n8n | {item['codigo']}] -> {item['retorno_n8n']}\n")
            else:
                print(f"[n8n | {item['codigo']}] Aviso -> {item['mensagem']}\n")


if __name__ == "__main__":
    main()
