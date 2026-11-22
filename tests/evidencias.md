# Evidências de Testes — Agente de Análise de Estoque

**Data/hora da execução:** 22/11/2026 12:03:22

## Como reproduzir

1. Mantenha a API de Estoque rodando em `http://127.0.0.1:8000`.
2. Mantenha o workflow `Alerta de Estoque Crítico` publicado no n8n em `http://localhost:5678`.
3. Na raiz deste repositório (com `.venv` ativo e `.env` configurado), execute:

```powershell
python -m tests.run_tests
```

## Resumo dos cenários

| # | Cenário | Iterações | Ferramentas | Retorno n8n | Status |
|---|---|---:|---|---|---|
| 1 | Análise de estoque baixo — PRD-001 (Obrigatório) | 2 | `consultar_produto` | `ALERTA_ENVIADO` | **PASSOU** |
| 2 | Consulta de produto inexistente — PRD-999 / HTTP 404 (Obrigatório) | 2 | `consultar_produto` | `Não acionado` | **PASSOU** |
| 3 | Comportamento alternativo — pergunta conceitual sem API (Obrigatório) | 1 | `nenhuma` | `Não acionado` | **PASSOU** |
| 4 | Caso de borda no limite mínimo — PRD-005 (30/30 pct) (Bônus) | 2 | `consultar_produto` | `ALERTA_ENVIADO` | **PASSOU** |
| 5 | Produto em estoque normal — PRD-002 / ramo false do IF no n8n (Bônus) | 2 | `consultar_produto` | `SEM_ALERTA` | **PASSOU** |
| 6 | Solicitação fora do escopo e operação não autorizada (Bônus) | 1 | `nenhuma` | `Não acionado` | **PASSOU** |
| 7 | Indisponibilidade simulada da API — PRD-503 / HTTP 503 (Bônus) | 2 | `consultar_produto` | `Não acionado` | **PASSOU** |

## Cenário 1 — Análise de estoque baixo — PRD-001 (Obrigatório)

- **Entrada:** `Qual a situação do estoque do produto PRD-001?`
- **Resultado esperado:** Chamar consultar_produto(PRD-001), retornar situacao='estoque_baixo' (5 de 10 un) e o nó notificar_n8n receber ALERTA_ENVIADO do workflow.
- **Status da validação:** **PASSOU**
- **Iterações no LangGraph:** `2`
- **Ferramentas acionadas:** `consultar_produto`

### Resposta observada do agente

**Produto:** PRD-001 – *Mouse sem fio*  
**Quantidade atual:** 5 un  
**Estoque mínimo:** 10 un  
**Unidade:** un  

**Situação (classificação oficial):** **estoque_baixo**  
- A quantidade está abaixo do estoque mínimo, portanto o item requer reposição.  
- Como `no_limite_exato` é **false**, o produto ainda não atingiu exatamente o limite mínimo, mas já está em nível crítico.  

**Recomendação:** Planejar a reposição o quanto antes para evitar ruptura de estoque.

### Evidência técnica (logs de ferramentas e n8n)

```json
{
  "ferramentas_chamadas": [
    {
      "nome": "consultar_produto",
      "args": {
        "codigo": "PRD-001"
      }
    }
  ],
  "resultados_tools": [
    {
      "tool": "consultar_produto",
      "conteudo": "{\"sucesso\": true, \"produto\": {\"codigo\": \"PRD-001\", \"nome\": \"Mouse sem fio\", \"categoria\": \"Periféricos\", \"quantidade_atual\": 5, \"estoque_minimo\": 10, \"unidade\": \"un\", \"situacao\": \"estoque_baixo\", \"no_limite_exato\": false, \"requer_reposicao\": true}}"
    }
  ],
  "alertas_n8n": [
    {
      "codigo": "PRD-001",
      "situacao": "estoque_baixo",
      "enviado": true,
      "status_http": 200,
      "retorno_n8n": {
        "status_alerta": "ALERTA_ENVIADO",
        "prioridade": "ALTA",
        "mensagem_alerta": "Reposição necessária para PRD-001 (Mouse sem fio): 5 un disponíveis (mínimo: 10).",
        "registrado_em": "2026-11-22T12:03:25.211-03:00"
      }
    }
  ]
}
```

## Cenário 2 — Consulta de produto inexistente — PRD-999 / HTTP 404 (Obrigatório)

- **Entrada:** `Verifique o estoque do produto PRD-999.`
- **Resultado esperado:** Chamar consultar_produto(PRD-999), tratar HTTP 404 (produto_nao_encontrado) sem inventar dados e sem acionar o n8n.
- **Status da validação:** **PASSOU**
- **Iterações no LangGraph:** `2`
- **Ferramentas acionadas:** `consultar_produto`

### Resposta observada do agente

O produto **PRD-999** não foi localizado na base de estoque.

**Detalhes do erro retornado pela API**  
- **Código do erro:** `produto_nao_encontrado`  
- **Mensagem:** “Produto PRD-999 não encontrado na base de estoque.”

Como o item não consta no sistema, não há informações de quantidade, estoque mínimo ou situação para relatar. Caso tenha digitado o código incorretamente ou deseje consultar outro produto, por favor informe o código correto ou outro identificador. Estou à disposição para ajudar!

### Evidência técnica (logs de ferramentas e n8n)

```json
{
  "ferramentas_chamadas": [
    {
      "nome": "consultar_produto",
      "args": {
        "codigo": "PRD-999"
      }
    }
  ],
  "resultados_tools": [
    {
      "tool": "consultar_produto",
      "conteudo": "{\"sucesso\": false, \"erro\": \"produto_nao_encontrado\", \"mensagem\": \"Produto PRD-999 não encontrado na base de estoque.\"}"
    }
  ],
  "alertas_n8n": []
}
```

## Cenário 3 — Comportamento alternativo — pergunta conceitual sem API (Obrigatório)

- **Entrada:** `O que significa estoque mínimo na gestão de inventário?`
- **Resultado esperado:** Responder diretamente pela transição condicional sem chamar ferramentas (iteracoes == 1) e sem acionar o n8n.
- **Status da validação:** **PASSOU**
- **Iterações no LangGraph:** `1`
- **Ferramentas acionadas:** `nenhuma`

### Resposta observada do agente

**Estoque mínimo** (ou *estoque de segurança*) é a quantidade mínima de um item que a empresa decide manter em seu armazém para garantir que a demanda dos clientes seja atendida mesmo diante de variações inesperadas, como atrasos na reposição, aumento súbito de vendas ou falhas na produção.

### Por que ele é importante?
1. **Evita rupturas (stock‑out)** – Quando a quantidade em estoque cai abaixo do nível de atendimento da demanda, a empresa pode perder vendas e a confiança do cliente.
2. **Compensa incertezas** – A demanda e o tempo de reposição raramente são perfeitamente previsíveis; o estoque mínimo funciona como uma “almofada” contra essas variações.
3. **Planejamento de reposição** – Quando o estoque atual atinge ou fica próximo ao estoque mínimo, o sistema de gestão de inventário costuma gerar alertas ou ordens de compra para reabastecer o item antes que ele se esgote.

### Como ele é definido?
- **Análise histórica de demanda**: média de consumo diário ou semanal, considerando sazonalidade.
- **Tempo de reposição (lead time)**: quanto tempo leva desde a ordem de compra até a chegada do produto.
- **Nível de serviço desejado**: probabilidade de atender a demanda sem falta (ex.: 95 % de serviço).
- **Variabilidade**: flutuações tanto na demanda quanto no lead time.

A fórmula mais simples costuma ser:

\[
\text{Estoque Mínimo} = \text{Consumo Médio Diário} \times \text{Lead Time} \times \text{Fator de Segurança}
\]

O **fator de segurança** reflete o nível de risco que a empresa está disposta a aceitar; quanto maior o fator, maior será o estoque mínimo.

### Diferença entre estoque mínimo e estoque de segurança
- **Estoque mínimo**: ponto de disparo que indica quando iniciar a reposição (geralmente usado como limite de alerta no sistema).
- **Estoque de segurança**: quantidade adicional mantida acima do estoque mínimo para absorver variações inesperadas. Em muitas empresas, os dois conceitos são combinados em um único número chamado “estoque mínimo”.

Em resumo, o estoque mínimo serve como um gatilho de controle: quando a quantidade disponível de um item chega a esse nível, a equipe de compras ou o sistema automatizado deve agir para reabastecer, evitando assim a ruptura de estoque e garantindo a continuidade das operações.

### Evidência técnica (logs de ferramentas e n8n)

```json
{
  "ferramentas_chamadas": [],
  "resultados_tools": [],
  "alertas_n8n": []
}
```

## Cenário 4 — Caso de borda no limite mínimo — PRD-005 (30/30 pct) (Bônus)

- **Entrada:** `Analise a situação do produto PRD-005.`
- **Resultado esperado:** Classificar PRD-005 (30/30 pct) como estoque_baixo com no_limite_exato=true e disparar ALERTA_ENVIADO no n8n.
- **Status da validação:** **PASSOU**
- **Iterações no LangGraph:** `2`
- **Ferramentas acionadas:** `consultar_produto`

### Resposta observada do agente

**Produto analisado:** PRD-005  
**Nome:** Papel sulfite A4  
**Categoria:** Papelaria  
**Quantidade atual:** 30 pct  
**Estoque mínimo:** 30 pct  
**Situação (classificação oficial):** **estoque_baixo**  

**Observação importante:** o campo `no_limite_exato` está marcado como **true**, o que indica que a quantidade atual atingiu exatamente o limite mínimo estabelecido. Isso requer atenção imediata e reposição preventiva para evitar que o item fique esgotado.  

**Recomendação:** providenciar a reposição do produto o quanto antes, considerando que já está no ponto crítico de estoque.

### Evidência técnica (logs de ferramentas e n8n)

```json
{
  "ferramentas_chamadas": [
    {
      "nome": "consultar_produto",
      "args": {
        "codigo": "PRD-005"
      }
    }
  ],
  "resultados_tools": [
    {
      "tool": "consultar_produto",
      "conteudo": "{\"sucesso\": true, \"produto\": {\"codigo\": \"PRD-005\", \"nome\": \"Papel sulfite A4\", \"categoria\": \"Papelaria\", \"quantidade_atual\": 30, \"estoque_minimo\": 30, \"unidade\": \"pct\", \"situacao\": \"estoque_baixo\", \"no_limite_exato\": true, \"requer_reposicao\": true}}"
    }
  ],
  "alertas_n8n": [
    {
      "codigo": "PRD-005",
      "situacao": "estoque_baixo",
      "enviado": true,
      "status_http": 200,
      "retorno_n8n": {
        "status_alerta": "ALERTA_ENVIADO",
        "prioridade": "ALTA",
        "mensagem_alerta": "Reposição necessária para PRD-005 (Papel sulfite A4): 30 pct disponíveis (mínimo: 30).",
        "registrado_em": "2026-11-22T12:03:29.294-03:00"
      }
    }
  ]
}
```

## Cenário 5 — Produto em estoque normal — PRD-002 / ramo false do IF no n8n (Bônus)

- **Entrada:** `Qual a situação do produto PRD-002?`
- **Resultado esperado:** Classificar PRD-002 (40/15 un) como normal, enviar ao n8n e exercitar o ramo false do nó IF retornando SEM_ALERTA.
- **Status da validação:** **PASSOU**
- **Iterações no LangGraph:** `2`
- **Ferramentas acionadas:** `consultar_produto`

### Resposta observada do agente

**Produto:** PRD-002  
**Nome:** Teclado USB  
**Categoria:** Periféricos  
**Quantidade atual:** 40 un  
**Estoque mínimo:** 15 un  
**Unidade:** un  

**Situação (classificação oficial):** **normal** – a quantidade atual está acima do estoque mínimo.  

**Necessidade de reposição:** Não há necessidade de reposição neste momento, pois o produto está em situação normal.

### Evidência técnica (logs de ferramentas e n8n)

```json
{
  "ferramentas_chamadas": [
    {
      "nome": "consultar_produto",
      "args": {
        "codigo": "PRD-002"
      }
    }
  ],
  "resultados_tools": [
    {
      "tool": "consultar_produto",
      "conteudo": "{\"sucesso\": true, \"produto\": {\"codigo\": \"PRD-002\", \"nome\": \"Teclado USB\", \"categoria\": \"Periféricos\", \"quantidade_atual\": 40, \"estoque_minimo\": 15, \"unidade\": \"un\", \"situacao\": \"normal\", \"no_limite_exato\": false, \"requer_reposicao\": false}}"
    }
  ],
  "alertas_n8n": [
    {
      "codigo": "PRD-002",
      "situacao": "normal",
      "enviado": true,
      "status_http": 200,
      "retorno_n8n": {
        "status_alerta": "SEM_ALERTA",
        "mensagem": "Estoque dentro do nível normal."
      }
    }
  ]
}
```

## Cenário 6 — Solicitação fora do escopo e operação não autorizada (Bônus)

- **Entrada:** `Cadastre um produto novo PRD-099 e me diga a previsão do tempo para amanhã.`
- **Resultado esperado:** Recusar o cadastro (somente leitura) e recusar o tema fora do escopo de estoque, sem chamar ferramentas.
- **Status da validação:** **PASSOU**
- **Iterações no LangGraph:** `1`
- **Ferramentas acionadas:** `nenhuma`

### Resposta observada do agente

Desculpe, mas eu só realizo consultas e análises de estoque. Não tenho permissão para cadastrar novos produtos nem para fornecer previsões do tempo. Se precisar de informações sobre a situação ou disponibilidade de algum item já existente no estoque, estou à disposição para ajudar.

### Evidência técnica (logs de ferramentas e n8n)

```json
{
  "ferramentas_chamadas": [],
  "resultados_tools": [],
  "alertas_n8n": []
}
```

## Cenário 7 — Indisponibilidade simulada da API — PRD-503 / HTTP 503 (Bônus)

- **Entrada:** `Consulte o produto PRD-503.`
- **Resultado esperado:** Tratar HTTP 503 (servico_indisponivel) de forma controlada sem inventar dados.
- **Status da validação:** **PASSOU**
- **Iterações no LangGraph:** `2`
- **Ferramentas acionadas:** `consultar_produto`

### Resposta observada do agente

A consulta ao produto **PRD-503** não pôde ser concluída porque o serviço da API de Estoque está temporariamente indisponível:

- **Código de erro:** `servico_indisponivel`
- **Mensagem:** “Serviço temporariamente indisponível. Tente novamente mais tarde.”

Por favor, tente a consulta novamente em alguns minutos. Caso o problema persista, avise-me que tentaremos outra abordagem ou verificaremos se há alguma alternativa disponível.

### Evidência técnica (logs de ferramentas e n8n)

```json
{
  "ferramentas_chamadas": [
    {
      "nome": "consultar_produto",
      "args": {
        "codigo": "PRD-503"
      }
    }
  ],
  "resultados_tools": [
    {
      "tool": "consultar_produto",
      "conteudo": "{\"sucesso\": false, \"erro\": \"servico_indisponivel\", \"mensagem\": \"Serviço temporariamente indisponível. Tente novamente mais tarde.\"}"
    }
  ],
  "alertas_n8n": []
}
```
