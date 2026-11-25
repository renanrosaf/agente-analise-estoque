# Evidências de Testes — Agente de Análise de Estoque

**Data/hora da execução:** 25/11/2026 20:10:45

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
| 11 | Listagem geral e resumo consolidado — listar_produtos (Adicional) | 2 | `listar_produtos` | `ALERTA_ENVIADO (ALTA), SEM_ALERTA, SEM_ALERTA, ALERTA_ENVIADO (URGENTE), ALERTA_ENVIADO (ALTA), SEM_ALERTA, ALERTA_ENVIADO (ALTA), ALERTA_ENVIADO (URGENTE), ALERTA_ENVIADO (ALTA), SEM_ALERTA, ALERTA_ENVIADO (ALTA), SEM_ALERTA` | **PASSOU** |

## Cenário 1 — Análise de estoque baixo — PRD-001 (Obrigatório)

- **Entrada:** `Qual a situação do estoque do produto PRD-001?`
- **Resultado esperado:** Classificar PRD-001 (5/10 un) como estoque_baixo e receber ALERTA_ENVIADO (prioridade ALTA) do n8n, sem expor campos técnicos.
- **Status da validação:** **PASSOU**
- **Iterações no LangGraph:** `2`
- **Ferramentas acionadas:** `consultar_produto`

### Resposta observada do agente

**Produto:** PRD-001 – *Mouse sem fio*  
**Quantidade atual:** 5 un  
**Estoque mínimo:** 10 un  
**Situação:** estoque baixo (abaixo do limite mínimo)  
**Necessidade de reposição:** sim – o nível está abaixo do mínimo e requer reposição preventiva.

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
        "registrado_em": "2026-11-25T20:10:46.764-03:00"
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

O código **PRD‑999** não foi localizado na base de estoque. Isso significa que não há registro desse produto no sistema. Se o código estiver correto, pode ser necessário verificar se o item foi cadastrado ou se há algum erro de digitação. Caso precise consultar outro produto ou obter informações diferentes, estou à disposição.

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

- **Objetivo:** garantir que, mesmo diante de variações na demanda ou pequenos atrasos nas reposições, o item não se torne indisponível para os clientes ou para a produção.  
- **Como é determinado:** normalmente considera‑se o tempo médio de reposição (lead time), a demanda prevista nesse período e um fator de segurança (por exemplo, 10 % a mais). A fórmula simplificada costuma ser:  

\[
\text{Estoque mínimo} = (\text{Consumo diário médio} \times \text{Tempo de reposição em dias}) + \text{Margem de segurança}
\]

- **Quando o estoque atinge esse limite:** o item entra em situação de “estoque baixo” e, embora ainda haja unidades disponíveis, recomenda‑se iniciar o processo de reposição para evitar que ele chegue a zero (esgotado).  

Manter um estoque mínimo bem calculado ajuda a equilibrar dois aspectos críticos da gestão de inventário: **a disponibilidade de produtos** (evitando rupturas) e **o custo de manutenção de estoque** (evitando excessos).

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

A situação do item foi classificada como **estoque baixo**. Como a quantidade disponível está exatamente no limite mínimo, o produto atingiu o ponto crítico e requer reposição preventiva para evitar que se torne esgotado. Recomenda‑se providenciar a reposição o quanto antes.

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
        "registrado_em": "2026-11-25T20:10:50.339-03:00"
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

O produto **PRD-002 – Teclado USB** possui atualmente **40 unidades** em estoque, com um estoque mínimo definido em **15 unidades**. A situação classificada pelo sistema é **normal**, ou seja, a quantidade disponível está acima do limite mínimo. Não há necessidade de reposição neste momento.

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
**Situação:** esgotado  

Como a quantidade está em zero, o item está fora de estoque e necessita de reposição imediata.

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
        "registrado_em": "2026-11-25T20:11:15.721-03:00"
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

Para consultar o estoque preciso do código do produto no formato correto (por exemplo, **PRD-001**). O código que você informou (**ABC-1**) não corresponde ao padrão esperado. Poderia, por favor, fornecer o código do produto no formato **PRD‑XXX**? Assim poderei buscar a informação de estoque para você.

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

Para poder verificar a disponibilidade, preciso que você informe o código do produto (por exemplo, **PRD‑001**) ou, ao menos, o nome completo do item que deseja consultar. Poderia me fornecer esses detalhes?

### Evidência técnica (logs de ferramentas e n8n)

```json
{
  "ferramentas_chamadas": [],
  "resultados_tools": [],
  "alertas_n8n": []
}
```

## Cenário 11 — Listagem geral e resumo consolidado — listar_produtos (Adicional)

- **Entrada:** `Quantos produtos precisam de reposição no estoque?`
- **Resultado esperado:** Chamar listar_produtos, retornar resumo consolidado (12 itens, 7 requerem reposição sendo 2 no limite) e responder 7 sem citar campos técnicos.
- **Status da validação:** **PASSOU**
- **Iterações no LangGraph:** `2`
- **Ferramentas acionadas:** `listar_produtos`

### Resposta observada do agente

De acordo com a consulta ao estoque, **7 produtos** estão classificados como que **necessitam de reposição**.  

Esses 7 itens englobam:

* os que estão **esgotados** (quantidade = 0)  
* os que estão em **estoque baixo**, inclusive aqueles que atingiram exatamente o estoque mínimo (ex.: quantidade = estoque mínimo).

Portanto, no momento há **sete produtos** que requerem reposição para evitar falta de disponibilidade.

### Evidência técnica (logs de ferramentas e n8n)

```json
{
  "ferramentas_chamadas": [
    {
      "nome": "listar_produtos",
      "args": {
        "categoria": null
      }
    }
  ],
  "resultados_tools": [
    {
      "tool": "listar_produtos",
      "conteudo": "{\"sucesso\": true, \"total\": 12, \"resumo\": {\"esgotado\": 2, \"estoque_baixo\": 5, \"estoque_baixo_no_limite\": 2, \"normal\": 5, \"requerem_reposicao\": 7}, \"produtos\": [{\"codigo\": \"PRD-001\", \"nome\": \"Mouse sem fio\", \"categoria\": \"Periféricos\", \"quantidade_atual\": 5, \"estoque_minimo\": 10, \"unidade\": \"un\", \"situacao\": \"estoque_baixo\", \"no_limite_exato\": false, \"requer_reposicao\": true}, {\"codigo\": \"PRD-002\", \"nome\": \"Teclado USB\", \"categoria\": \"Periféricos\", \"quantidade_atual\": 40, \"estoque_minimo\": 15, \"unidade\": \"un\", \"situacao\": \"normal\", \"no_limite_exato\": false, \"requer_reposicao\": false}, {\"codigo\": \"PRD-003\", \"nome\": \"Monitor 24 polegadas\", \"categoria\": \"Monitores\", \"quantidade_atual\": 12, \"estoque_minimo\": 5, \"unidade\": \"un\", \"situacao\": \"normal\", \"no_limite_exato\": false, \"requer_reposicao\": false}, {\"codigo\": \"PRD-004\", \"nome\": \"Cabo HDMI 2 m\", \"categoria\": \"Cabos e Adaptadores\", \"quantidade_atual\": 0, \"estoque_minimo\": 20, \"unidade\": \"un\", \"situacao\": \"esgotado\", \"no_limite_exato\": false, \"requer_reposicao\": true}, {\"codigo\": \"PRD-005\", \"nome\": \"Papel sulfite A4\", \"categoria\": \"Papelaria\", \"quantidade_atual\": 30, \"estoque_minimo\": 30, \"unidade\": \"pct\", \"situacao\": \"estoque_baixo\", \"no_limite_exato\": true, \"requer_reposicao\": true}, {\"codigo\": \"PRD-006\", \"nome\": \"Caneta esferográfica azul\", \"categoria\": \"Papelaria\", \"quantidade_atual\": 200, \"estoque_minimo\": 50, \"unidade\": \"un\", \"situacao\": \"normal\", \"no_limite_exato\": false, \"requer_reposicao\": false}, {\"codigo\": \"PRD-007\", \"nome\": \"Cartucho de tinta preta\", \"categoria\": \"Suprimentos de Impressão\", \"quantidade_atual\": 3, \"estoque_minimo\": 8, \"unidade\": \"un\", \"situacao\": \"estoque_baixo\", \"no_limite_exato\": false, \"requer_reposicao\": true}, {\"codigo\": \"PRD-008\", \"nome\": \"Webcam Full HD\", \"categoria\": \"Periféricos\", \"quantidade_atual\": 0, \"estoque_minimo\": 5, \"unidade\": \"un\", \"situacao\": \"esgotado\", \"no_limite_exato\": false, \"requer_reposicao\": true}, {\"codigo\": \"PRD-009\", \"nome\": \"Notebook 14 polegadas\", \"categoria\": \"Computadores\", \"quantidade_atual\": 8, \"estoque_minimo\": 8, \"unidade\": \"un\", \"situacao\": \"estoque_baixo\", \"no_limite_exato\": true, \"requer_reposicao\": true}, {\"codigo\": \"PRD-010\", \"nome\": \"Pen drive 64 GB\", \"categoria\": \"Armazenamento\", \"quantidade_atual\": 25, \"estoque_minimo\": 10, \"unidade\": \"un\", \"situacao\": \"normal\", \"no_limite_exato\": false, \"requer_reposicao\": false}, {\"codigo\": \"PRD-011\", \"nome\": \"Álcool isopropílico\", \"categoria\": \"Limpeza\", \"quantidade_atual\": 4, \"estoque_minimo\": 10, \"unidade\": \"L\", \"situacao\": \"estoque_baixo\", \"no_limite_exato\": false, \"requer_reposicao\": true}, {\"codigo\": \"PRD-012\", \"nome\": \"Cabo de rede Cat6\", \"categoria\": \"Cabos e Adaptadores\", \"quantidade_atual\": 150, \"estoque_minimo\": 100, \"unidade\": \"m\", \"situacao\": \"normal\", \"no_limite_exato\": false, \"requer_reposicao\": false}], \"registros_invalidos\": []}"
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
        "registrado_em": "2026-11-25T20:11:42.167-03:00"
      }
    },
    {
      "codigo": "PRD-002",
      "situacao": "normal",
      "enviado": true,
      "status_http": 200,
      "retorno_n8n": {
        "status_alerta": "SEM_ALERTA",
        "mensagem": "Estoque dentro do nível normal."
      }
    },
    {
      "codigo": "PRD-003",
      "situacao": "normal",
      "enviado": true,
      "status_http": 200,
      "retorno_n8n": {
        "status_alerta": "SEM_ALERTA",
        "mensagem": "Estoque dentro do nível normal."
      }
    },
    {
      "codigo": "PRD-004",
      "situacao": "esgotado",
      "enviado": true,
      "status_http": 200,
      "retorno_n8n": {
        "status_alerta": "ALERTA_ENVIADO",
        "prioridade": "URGENTE",
        "mensagem_alerta": "Reposição necessária para PRD-004 (Cabo HDMI 2 m): 0 un disponíveis (mínimo: 20).",
        "registrado_em": "2026-11-25T20:11:42.305-03:00"
      }
    },
    {
      "codigo": "PRD-005",
      "situacao": "estoque_baixo",
      "enviado": true,
      "status_http": 200,
      "retorno_n8n": {
        "status_alerta": "ALERTA_ENVIADO",
        "prioridade": "ALTA",
        "mensagem_alerta": "Reposição necessária para PRD-005 (Papel sulfite A4): 30 pct disponíveis (mínimo: 30).",
        "registrado_em": "2026-11-25T20:11:42.353-03:00"
      }
    },
    {
      "codigo": "PRD-006",
      "situacao": "normal",
      "enviado": true,
      "status_http": 200,
      "retorno_n8n": {
        "status_alerta": "SEM_ALERTA",
        "mensagem": "Estoque dentro do nível normal."
      }
    },
    {
      "codigo": "PRD-007",
      "situacao": "estoque_baixo",
      "enviado": true,
      "status_http": 200,
      "retorno_n8n": {
        "status_alerta": "ALERTA_ENVIADO",
        "prioridade": "ALTA",
        "mensagem_alerta": "Reposição necessária para PRD-007 (Cartucho de tinta preta): 3 un disponíveis (mínimo: 8).",
        "registrado_em": "2026-11-25T20:11:42.427-03:00"
      }
    },
    {
      "codigo": "PRD-008",
      "situacao": "esgotado",
      "enviado": true,
      "status_http": 200,
      "retorno_n8n": {
        "status_alerta": "ALERTA_ENVIADO",
        "prioridade": "URGENTE",
        "mensagem_alerta": "Reposição necessária para PRD-008 (Webcam Full HD): 0 un disponíveis (mínimo: 5).",
        "registrado_em": "2026-11-25T20:11:42.462-03:00"
      }
    },
    {
      "codigo": "PRD-009",
      "situacao": "estoque_baixo",
      "enviado": true,
      "status_http": 200,
      "retorno_n8n": {
        "status_alerta": "ALERTA_ENVIADO",
        "prioridade": "ALTA",
        "mensagem_alerta": "Reposição necessária para PRD-009 (Notebook 14 polegadas): 8 un disponíveis (mínimo: 8).",
        "registrado_em": "2026-11-25T20:11:42.495-03:00"
      }
    },
    {
      "codigo": "PRD-010",
      "situacao": "normal",
      "enviado": true,
      "status_http": 200,
      "retorno_n8n": {
        "status_alerta": "SEM_ALERTA",
        "mensagem": "Estoque dentro do nível normal."
      }
    },
    {
      "codigo": "PRD-011",
      "situacao": "estoque_baixo",
      "enviado": true,
      "status_http": 200,
      "retorno_n8n": {
        "status_alerta": "ALERTA_ENVIADO",
        "prioridade": "ALTA",
        "mensagem_alerta": "Reposição necessária para PRD-011 (Álcool isopropílico): 4 L disponíveis (mínimo: 10).",
        "registrado_em": "2026-11-25T20:11:42.575-03:00"
      }
    },
    {
      "codigo": "PRD-012",
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
