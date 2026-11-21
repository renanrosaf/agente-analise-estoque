from src.graph import executar_agente
from src.n8n_client import notificar_produtos_criticos


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
        print(f"\n[Log] Iterações: {resultado['iteracoes']} | Ferramentas usadas: {tools or 'nenhuma'}")
        print(f"Agente:\n{resultado['resposta']}\n")

        alertas = notificar_produtos_criticos(resultado["resultados_tools"])
        for alerta in alertas:
            if alerta.get("enviado"):
                print(f"[n8n] Alerta registrado -> {alerta['retorno_n8n']}\n")
            else:
                print(f"[n8n] Aviso -> {alerta['mensagem']}\n")


if __name__ == "__main__":
    main()