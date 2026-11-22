from typing import Annotated, Any, TypedDict

from langchain_core.messages import AIMessage, AnyMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_groq import ChatGroq
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

from src.config import GROQ_API_KEY, GROQ_MODEL, validar_configuracao
from src.n8n_client import processar_notificacoes_n8n
from src.tools import TOOLS

MAX_ITERACOES = 5

SYSTEM_PROMPT = """# Papel
Você é um agente analista de estoque técnico, objetivo e confiável.

# Objetivo
Interpretar solicitações relacionadas à disponibilidade e à situação do estoque de produtos, consultar a API de Estoque por meio das ferramentas disponíveis quando necessário e produzir respostas claras e verificáveis.

# Contexto
- As ferramentas já retornam cada produto com a classificação oficial calculada em Python no campo `situacao`:
  - `esgotado`: quantidade_atual == 0
  - `estoque_baixo`: 0 < quantidade_atual <= estoque_minimo (inclui o limite exato, sinalizado por `no_limite_exato: true`)
  - `normal`: quantidade_atual > estoque_minimo
- Use exatamente o campo `situacao` retornado pela ferramenta — nunca recalcule nem contradiga esse valor. Quando `no_limite_exato` for `true`, destaque explicitamente que o item atingiu exatamente o limite mínimo e requer atenção/reposição preventiva.

# Restrições
1. Só chame ferramentas quando a solicitação exigir consultar produtos, quantidades ou categorias na API.
2. Para perguntas conceituais sobre gestão de estoque (ex.: "o que é estoque mínimo?"), responda diretamente SEM chamar nenhuma ferramenta.
3. Para solicitações ambíguas (ex.: falta código ou categoria para identificar o produto), peça esclarecimento ao usuário sem chutar códigos.
4. Para solicitações fora do escopo de análise de estoque (ex.: previsão do tempo, receitas, esportes), informe educadamente que você atua apenas na análise de estoque e não chame ferramentas.
5. Nunca cadastre, altere ou exclua produtos. Se o usuário pedir para cadastrar, editar ou apagar itens, recuse de forma clara explicando que o agente opera apenas em modo de consulta e análise.
6. Nunca invente códigos, nomes, quantidades ou preços. Em caso de erro da API (404, 422, 503 ou conexão), explique o erro retornado de forma transparente.
7. Ao analisar um produto existente, informe sempre: código, nome, quantidade atual, estoque mínimo, unidade, situação classificada e necessidade de reposição.
"""


class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    iteracoes: int
    alertas_n8n: list[dict[str, Any]]


def _extrair_texto(conteudo: Any) -> str:
    """Garante retorno em texto limpo mesmo se o modelo devolver lista de blocos."""
    if isinstance(conteudo, str):
        return conteudo.strip()
    if isinstance(conteudo, list):
        partes = [
            bloco.get("text", "") if isinstance(bloco, dict) else str(bloco)
            for bloco in conteudo
        ]
        return "\n".join(p for p in partes if p).strip()
    return str(conteudo).strip()


def criar_grafo():
    validar_configuracao()

    llm = ChatGroq(
        model=GROQ_MODEL,
        api_key=GROQ_API_KEY,
        temperature=0,
        timeout=30,
        max_retries=2,
    ).bind_tools(TOOLS)

    def no_agente(state: AgentState) -> dict[str, Any]:
        mensagens = [SystemMessage(content=SYSTEM_PROMPT), *state["messages"]]
        resposta = llm.invoke(mensagens)
        return {
            "messages": [resposta],
            "iteracoes": state.get("iteracoes", 0) + 1,
        }

    no_ferramentas = ToolNode(TOOLS)

    def no_notificar_n8n(state: AgentState) -> dict[str, Any]:
        """Nó complementar do grafo que envia os produtos consultados ao Webhook do n8n."""
        tool_messages = [m for m in state["messages"] if isinstance(m, ToolMessage)]
        alertas = processar_notificacoes_n8n(tool_messages) if tool_messages else []
        return {"alertas_n8n": alertas}

    def decidir_proximo_passo(state: AgentState) -> str:
        if state.get("iteracoes", 0) >= MAX_ITERACOES:
            return "notificar_n8n"

        ultima_msg = state["messages"][-1]
        if isinstance(ultima_msg, AIMessage) and ultima_msg.tool_calls:
            return "ferramentas"
        return "notificar_n8n"

    builder = StateGraph(AgentState)
    builder.add_node("agente", no_agente)
    builder.add_node("ferramentas", no_ferramentas)
    builder.add_node("notificar_n8n", no_notificar_n8n)

    builder.add_edge(START, "agente")
    builder.add_conditional_edges(
        "agente",
        decidir_proximo_passo,
        {"ferramentas": "ferramentas", "notificar_n8n": "notificar_n8n"},
    )
    builder.add_edge("ferramentas", "agente")
    builder.add_edge("notificar_n8n", END)

    return builder.compile()


def executar_agente(pergunta: str) -> dict[str, Any]:
    """Executa uma solicitação no grafo LangGraph e retorna resposta, logs e retornos do n8n."""
    grafo = criar_grafo()
    estado_final = grafo.invoke(
        {"messages": [HumanMessage(content=pergunta)], "iteracoes": 0, "alertas_n8n": []},
        config={"recursion_limit": 14},
    )

    ferramentas_chamadas = []
    resultados_tools = []
    for msg in estado_final["messages"]:
        if isinstance(msg, AIMessage) and msg.tool_calls:
            for call in msg.tool_calls:
                ferramentas_chamadas.append({"nome": call["name"], "args": call["args"]})
        elif isinstance(msg, ToolMessage):
            resultados_tools.append({"tool": msg.name, "conteudo": msg.content})

    ultima_msg = estado_final["messages"][-1]
    resposta_final = _extrair_texto(ultima_msg.content)

    # Fallback explícito caso o agente atinja o limite máximo de iterações sem texto final
    if not resposta_final:
        resposta_final = (
            "Atingi o limite máximo de passos sem conseguir concluir a análise. "
            "Por favor, reformule sua solicitação com mais detalhes."
        )

    return {
        "pergunta": pergunta,
        "resposta": resposta_final,
        "iteracoes": estado_final.get("iteracoes", 0),
        "ferramentas_chamadas": ferramentas_chamadas,
        "resultados_tools": resultados_tools,
        "alertas_n8n": estado_final.get("alertas_n8n", []),
    }