from typing import Annotated, Any, TypedDict

from langchain_core.messages import AIMessage, AnyMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_groq import ChatGroq
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

from src.config import GROQ_API_KEY, GROQ_MODEL, validar_configuracao
from src.tools import TOOLS

MAX_ITERACOES = 5

SYSTEM_PROMPT = """Você é um agente analista de estoque objetivo e confiável.

Regras de classificação de estoque (sempre compare quantidade_atual com estoque_minimo):
- Esgotado: quantidade_atual == 0
- Estoque baixo: 0 < quantidade_atual < estoque_minimo
- No limite mínimo: quantidade_atual == estoque_minimo (quando > 0)
- Normal: quantidade_atual > estoque_minimo

Regras obrigatórias de comportamento:
1. Use as ferramentas SOMENTE quando a solicitação exigir consultar produtos, quantidades ou categorias na API de estoque.
2. Para perguntas puramente conceituais sobre gestão de estoque (ex.: "o que é estoque mínimo?"), responda diretamente SEM chamar nenhuma ferramenta.
3. Nunca invente códigos, nomes, quantidades ou preços. Baseie toda análise exclusivamente nos dados retornados pelas ferramentas.
4. Quando uma ferramenta retornar erro (produto inexistente, código inválido ou serviço indisponível), explique a situação com clareza ao usuário e não invente dados.
5. Ao analisar um produto existente, informe sempre: código, nome, quantidade atual, estoque mínimo, unidade, situação classificada e se há necessidade de reposição.
"""


class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    iteracoes: int


def _extrair_texto(conteudo: Any) -> str:
    """Garante retorno em texto limpo mesmo se o modelo devolver lista de blocos."""
    if isinstance(conteudo, str):
        return conteudo
    if isinstance(conteudo, list):
        partes = [
            bloco.get("text", "") if isinstance(bloco, dict) else str(bloco)
            for bloco in conteudo
        ]
        return "\n".join(p for p in partes if p).strip()
    return str(conteudo)


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

    def decidir_proximo_passo(state: AgentState) -> str:
        # Condição explícita de parada para evitar loops indefinidos
        if state.get("iteracoes", 0) >= MAX_ITERACOES:
            return END

        ultima_msg = state["messages"][-1]
        if isinstance(ultima_msg, AIMessage) and ultima_msg.tool_calls:
            return "ferramentas"
        return END

    builder = StateGraph(AgentState)
    builder.add_node("agente", no_agente)
    builder.add_node("ferramentas", no_ferramentas)

    builder.add_edge(START, "agente")
    builder.add_conditional_edges(
        "agente",
        decidir_proximo_passo,
        {"ferramentas": "ferramentas", END: END},
    )
    builder.add_edge("ferramentas", "agente")

    return builder.compile()


def executar_agente(pergunta: str) -> dict[str, Any]:
    """Executa uma solicitação no grafo e retorna resposta + metadados para auditoria e n8n."""
    grafo = criar_grafo()
    estado_final = grafo.invoke(
        {"messages": [HumanMessage(content=pergunta)], "iteracoes": 0},
        config={"recursion_limit": 12},
    )

    ferramentas_chamadas = []
    resultados_tools = []
    for msg in estado_final["messages"]:
        if isinstance(msg, AIMessage) and msg.tool_calls:
            for call in msg.tool_calls:
                ferramentas_chamadas.append({"nome": call["name"], "args": call["args"]})
        elif isinstance(msg, ToolMessage):
            resultados_tools.append({"tool": msg.name, "conteudo": msg.content})

    resposta_final = _extrair_texto(estado_final["messages"][-1].content)
    return {
        "pergunta": pergunta,
        "resposta": resposta_final,
        "iteracoes": estado_final.get("iteracoes", 0),
        "ferramentas_chamadas": ferramentas_chamadas,
        "resultados_tools": resultados_tools,
    }