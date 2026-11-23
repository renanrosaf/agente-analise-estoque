# Evidências de Testes — Agente de Análise de Estoque

**Data/hora da execução:** 23/11/2026 16:50:58

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
| 1 | Análise de estoque baixo — PRD-001 (Obrigatório) | 2 | `consultar_produto` | `ALERTA_ENVIADO (ALTA)` | **PASSOU** |
| 2 | Produto inexistente — PRD-999 / HTTP 404 (Obrigatório) | 2 | `consultar_produto` | `Não acionado` | **PASSOU** |
| 3 | Comportamento alternativo — pergunta conceitual sem API (Obrigatório) | 1 | `nenhuma` | `Não acionado` | **PASSOU** |
| 4 | Caso de borda no limite mínimo — PRD-005 (30/30 pct) (Adicional) | 2 | `consultar_produto` | `ALERTA_ENVIADO (ALTA)` | **PASSOU** |
| 5 | Estoque normal — PRD-002 / ramo false do IF no n8n (Adicional) | 2 | `consultar_produto` | `SEM_ALERTA` | **PASSOU** |
| 6 | Solicitação fora do escopo e operação não autorizada (Adicional) | 1 | `nenhuma` | `Não acionado` | **PASSOU** |
| 7 | Indisponibilidade simulada da API — PRD-503 / HTTP 503 (Adicional) | 2 | `consultar_produto` | `Não acionado` | **PASSOU** |
| 8 | Estoque esgotado — PRD-004 / prioridade URGENTE no n8n (Adicional) | 2 | `consultar_produto` | `ALERTA_ENVIADO (URGENTE)` | **PASSOU** |
| 9 | Código em formato inválido — ABC-1 (Adicional) | 1 | `nenhuma` | `Não acionado` | **PASSOU** |
| 10 | Solicitação ambígua sem código ou produto (Adicional) | 1 | `nenhuma` | `Não acionado` | **PASSOU** |

## Cenário 1 — Análise de estoque baixo — PRD-001 (Obrigatório)

- **Entrada:** `Qual a situação do estoque do produto PRD-001?`
- **Resultado esperado:** Classificar PRD-001 (5/10 un) como estoque_baixo e receber ALERTA_ENVIADO (prioridade ALTA) do n8n, sem expor campos técnicos.
- **Status da validação:** **PASSOU**
- **Iterações no LangGraph:** `2`
- **Ferramentas acionadas:** `consultar_produto`

### Resposta observada do agente

**Código:** PRD-001  
**Nome:** Mouse sem fio  
**Quantidade atual:** 5 un  
**Estoque mínimo:** 10 un  
**Unidade:** unidade  

**Situação:** estoque baixo (a quantidade está abaixo do estoque mínimo).  

Como o nível está abaixo do mínimo, há necessidade de reposição para evitar a falta do item.

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
        "registrado_em": "2026-11-23T16:51:01.371-03:00"
      }
    }
  ]
}
```

## Cenário 2 — Produto inexistente — PRD-999 / HTTP 404 (Obrigatório)

- **Entrada:** `Verifique o estoque do produto PRD-999.`
- **Resultado esperado:** Receber erro produto_nao_encontrado (HTTP 404), informar ausência sem inventar dados e não acionar n8n.
- **Status da validação:** **PASSOU**
- **Iterações no LangGraph:** `2`
- **Ferramentas acionadas:** `consultar_produto`

### Resposta observada do agente

O código **PRD-999** não corresponde a nenhum item registrado na base de estoque. Não foi possível localizar informações sobre esse produto. Se o código estiver incorreto ou se houver outro identificador que você possa fornecer, por favor, informe‑me para que eu possa consultar novamente.

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
- **Resultado esperado:** Responder diretamente pela transição condicional em 1 iteração sem chamar ferramentas nem n8n.
- **Status da validação:** **PASSOU**
- **Iterações no LangGraph:** `1`
- **Ferramentas acionadas:** `nenhuma`

### Resposta observada do agente

**Estoque mínimo** é a quantidade de unidades de um produto que a empresa define como o limite inferior aceitável para manter em seu depósito.  

- **Objetivo:** garantir que, mesmo diante de variações na demanda ou pequenos atrasos nas reposições, o item não fique indisponível para os clientes ou para a produção.  
- **Como é calculado:** normalmente considera‑se o consumo médio diário (ou semanal), o tempo de reposição do fornecedor (lead‑time) e um fator de segurança para imprevistos. A fórmula básica costuma ser:  

\[
\text{Estoque mínimo} = (\text{Consumo médio por período} \times \text{Lead‑time}) + \text{Margem de segurança}
\]

- **Uso na prática:** quando o saldo atual do produto atinge ou fica abaixo desse nível, o sistema de gestão de estoque sinaliza a necessidade de reposição preventiva, evitando rupturas.  

Manter um estoque mínimo bem dimensionado ajuda a equilibrar custos (evitando excesso de capital parado) e o nível de serviço (evitando falta de produtos).

### Evidência técnica (logs de ferramentas e n8n)

```json
{
  "ferramentas_chamadas": [],
  "resultados_tools": [],
  "alertas_n8n": []
}
```

## Cenário 4 — Caso de borda no limite mínimo — PRD-005 (30/30 pct) (Adicional)

- **Entrada:** `Analise a situação do produto PRD-005.`
- **Resultado esperado:** Classificar PRD-005 como estoque_baixo com no_limite_exato=true e receber ALERTA_ENVIADO (ALTA) do n8n, explicando em linguagem natural.
- **Status da validação:** **PASSOU**
- **Iterações no LangGraph:** `2`
- **Ferramentas acionadas:** `consultar_produto`

### Resposta observada do agente

**Código:** PRD-005  
**Nome:** Papel sulfite A4  
**Quantidade atual:** 30 unidades (pacotes)  
**Estoque mínimo:** 30 unidades (pacotes)  
**Unidade:** pct  

**Situação:** estoque baixo  

O produto está exatamente no limite mínimo estabelecido. Isso indica que, embora ainda haja quantidade disponível, ele já atingiu o ponto crítico e requer reposição preventiva para evitar rupturas. Recomendo providenciar a reposição o quanto antes.

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
        "registrado_em": "2026-11-23T16:51:04.854-03:00"
      }
    }
  ]
}
```

## Cenário 5 — Estoque normal — PRD-002 / ramo false do IF no n8n (Adicional)

- **Entrada:** `Qual a situação do produto PRD-002?`
- **Resultado esperado:** Classificar PRD-002 (40/15 un) como normal e exercitar o ramo false do IF no n8n (SEM_ALERTA).
- **Status da validação:** **PASSOU**
- **Iterações no LangGraph:** `2`
- **Ferramentas acionadas:** `consultar_produto`

### Resposta observada do agente

O produto **PRD-002**, **Teclado USB**, possui atualmente **40 unidades** em estoque. O estoque mínimo definido para ele é de **15 unidades**. Como a quantidade disponível está acima desse limite, a situação está **normal** e **não há necessidade de reposição** no momento.

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

## Cenário 6 — Solicitação fora do escopo e operação não autorizada (Adicional)

- **Entrada:** `Cadastre um produto novo PRD-099 e me diga a previsão do tempo para amanhã.`
- **Resultado esperado:** Recusar o cadastro (somente leitura) e o tema fora do escopo sem chamar ferramentas nem n8n.
- **Status da validação:** **PASSOU**
- **Iterações no LangGraph:** `1`
- **Ferramentas acionadas:** `nenhuma`

### Resposta observada do agente

Desculpe, mas eu só realizo consultas e análises de estoque. Não posso cadastrar novos produtos nem fornecer previsões do tempo. Se precisar de informações sobre a situação de algum item já existente no estoque, estou à disposição para ajudar.

### Evidência técnica (logs de ferramentas e n8n)

```json
{
  "ferramentas_chamadas": [],
  "resultados_tools": [],
  "alertas_n8n": []
}
```

## Cenário 7 — Indisponibilidade simulada da API — PRD-503 / HTTP 503 (Adicional)

- **Entrada:** `Consulte o produto PRD-503.`
- **Resultado esperado:** Tratar servico_indisponivel (HTTP 503) de forma controlada sem inventar dados e sem acionar o n8n.
- **Status da validação:** **PASSOU**
- **Iterações no LangGraph:** `2`
- **Ferramentas acionadas:** `consultar_produto`

### Resposta observada do agente

Desculpe, não foi possível consultar o produto **PRD-503** porque o serviço da API de Estoque está temporariamente indisponível. Por favor, tente novamente mais tarde.

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

## Cenário 8 — Estoque esgotado — PRD-004 / prioridade URGENTE no n8n (Adicional)

- **Entrada:** `Qual a situação do estoque do produto PRD-004?`
- **Resultado esperado:** Classificar PRD-004 (0/20 un) como esgotado (requer_reposicao=true) e receber ALERTA_ENVIADO com prioridade URGENTE.
- **Status da validação:** **PASSOU**
- **Iterações no LangGraph:** `2`
- **Ferramentas acionadas:** `consultar_produto`

### Resposta observada do agente

**Código:** PRD-004  
**Nome:** Cabo HDMI 2 m  
**Quantidade atual:** 0 un  
**Estoque mínimo:** 20 un  

**Situação:** o produto está **esgotado**. Como não há unidades disponíveis, há necessidade imediata de reposição para atender a demanda.

### Evidência técnica (logs de ferramentas e n8n)

```json
{
  "ferramentas_chamadas": [
    {
      "nome": "consultar_produto",
      "args": {
        "codigo": "PRD-004"
      }
    }
  ],
  "resultados_tools": [
    {
      "tool": "consultar_produto",
      "conteudo": "{\"sucesso\": true, \"produto\": {\"codigo\": \"PRD-004\", \"nome\": \"Cabo HDMI 2 m\", \"categoria\": \"Cabos e Adaptadores\", \"quantidade_atual\": 0, \"estoque_minimo\": 20, \"unidade\": \"un\", \"situacao\": \"esgotado\", \"no_limite_exato\": false, \"requer_reposicao\": true}}"
    }
  ],
  "alertas_n8n": [
    {
      "codigo": "PRD-004",
      "situacao": "esgotado",
      "enviado": true,
      "status_http": 200,
      "retorno_n8n": {
        "status_alerta": "ALERTA_ENVIADO",
        "prioridade": "URGENTE",
        "mensagem_alerta": "Reposição necessária para PRD-004 (Cabo HDMI 2 m): 0 un disponíveis (mínimo: 20).",
        "registrado_em": "2026-11-23T16:51:39.139-03:00"
      }
    }
  ]
}
```

## Cenário 9 — Código em formato inválido — ABC-1 (Adicional)

- **Entrada:** `Qual o estoque do código ABC-1?`
- **Resultado esperado:** Rejeitar código fora do padrão PRD-XXX (codigo_invalido) e orientar o usuário sem acionar o n8n.
- **Status da validação:** **PASSOU**
- **Iterações no LangGraph:** `1`
- **Ferramentas acionadas:** `nenhuma`

### Resposta observada do agente

Para consultar o estoque preciso do código do produto no formato correto (por exemplo, **PRD-001**, **PRD-123** etc.). Poderia, por favor, informar o código do item seguindo esse padrão?

### Evidência técnica (logs de ferramentas e n8n)

```json
{
  "ferramentas_chamadas": [],
  "resultados_tools": [],
  "alertas_n8n": []
}
```

## Cenário 10 — Solicitação ambígua sem código ou produto (Adicional)

- **Entrada:** `Tem estoque disso?`
- **Resultado esperado:** Pedir esclarecimento ao usuário sem chutar códigos, sem chamar ferramentas e sem acionar o n8n.
- **Status da validação:** **PASSOU**
- **Iterações no LangGraph:** `1`
- **Ferramentas acionadas:** `nenhuma`

### Resposta observada do agente

Para poder verificar a disponibilidade, preciso que você informe o código do produto (por exemplo, **PRD-001**) ou o nome da categoria que deseja consultar. Poderia me fornecer esses detalhes?

### Evidência técnica (logs de ferramentas e n8n)

```json
{
  "ferramentas_chamadas": [],
  "resultados_tools": [],
  "alertas_n8n": []
}
```
