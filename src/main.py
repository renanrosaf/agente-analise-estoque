from src.graph import executar_agente


def main() -> None:
    print("=== LangGraph + Groq ===")
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
        print(f"\n[Log] Iterações: {resultado['iteracoes']} | Ferramentas usadas: {tools or 'nenhuma'}")
        print(f"Agente:\n{resultado['resposta']}\n")


if __name__ == "__main__":
    main()