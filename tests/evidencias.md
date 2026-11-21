# Evidências de Testes — Agente de Análise de Estoque

**Data/hora da execução:** 21/11/2026 15:21:45

## Como reproduzir

1. Mantenha a API de Estoque rodando em `http://127.0.0.1:8000`.
2. Mantenha o workflow `Alerta de Estoque Crítico` publicado no n8n em `http://localhost:5678`.
3. Na raiz deste repositório (com `.venv` ativo e `.env` configurado), execute:

```powershell
python -m tests.run_tests
```

## Resumo dos cenários

| # | Cenário | Iterações | Ferramentas | n8n | Status |
|---|---|---:|---|---|---|
| 1 | Análise de estoque de produto existente (Obrigatório) | 2 | `consultar_produto` | Alerta enviado | **PASSOU** |
| 2 | Consulta de produto inexistente — HTTP 404 (Obrigatório) | 2 | `consultar_produto` | Não acionado | **PASSOU** |
| 3 | Comportamento alternativo — pergunta conceitual sem chamar API (Obrigatório) | 1 | `nenhuma` | Não acionado | **PASSOU** |
| 4 | Indisponibilidade simulada da API — HTTP 503 (Bônus de confiabilidade) | 2 | `consultar_produto` | Não acionado | **PASSOU** |
| 5 | Validação de código em formato inválido — ABC-1 (Bônus de segurança) | 2 | `consultar_produto` | Não acionado | **PASSOU** |

## Cenário 1 — Análise de estoque de produto existente (Obrigatório)

- **Entrada:** `Qual a situação do estoque do produto PRD-001?`
- **Resultado esperado:** Chamar a ferramenta consultar_produto com PRD-001, identificar 5 un disponíveis frente ao estoque mínimo de 10 un, classificar como estoque baixo, recomendar reposição e acionar o alerta no webhook do n8n.
- **Status da validação:** **PASSOU**
- **Iterações no LangGraph:** `2`
- **Ferramentas acionadas:** `consultar_produto`

### Resposta observada do agente

**Código:** PRD-001  
**Nome:** Mouse sem fio  
**Quantidade atual:** 5 un  
**Estoque mínimo:** 10 un  
**Unidade:** un  

**Situação:** **Estoque baixo** (0 < quantidade atual < estoque mínimo)  

**Necessidade de reposição:** Sim – a quantidade está abaixo do nível mínimo e deve ser reposta para evitar falta de estoque.

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
      "conteudo": "{\"sucesso\": true, \"produto\": {\"codigo\": \"PRD-001\", \"nome\": \"Mouse sem fio\", \"categoria\": \"Periféricos\", \"quantidade_atual\": 5, \"estoque_minimo\": 10, \"unidade\": \"un\"}}"
    }
  ],
  "alertas_n8n": [
    {
      "enviado": true,
      "status_http": 200,
      "retorno_n8n": {
        "status_alerta": "ALERTA_ENVIADO",
        "prioridade": "ALTA",
        "mensagem_alerta": "Reposição necessária para PRD-001 (Mouse sem fio): 5 un disponíveis (mínimo: 10).",
        "registrado_em": "2026-11-21T15:21:47.772-03:00"
      }
    }
  ]
}
```

## Cenário 2 — Consulta de produto inexistente — HTTP 404 (Obrigatório)

- **Entrada:** `Verifique o estoque do produto PRD-999.`
- **Resultado esperado:** Chamar consultar_produto com PRD-999, receber erro 404 (produto_nao_encontrado) e informar a ausência do produto sem inventar quantidades.
- **Status da validação:** **PASSOU**
- **Iterações no LangGraph:** `2`
- **Ferramentas acionadas:** `consultar_produto`

### Resposta observada do agente

O produto **PRD-999** não foi encontrado na base de estoque (erro: *produto_nao_encontrado*). Como não há informações sobre quantidade atual, estoque mínimo ou unidade, não é possível classificar a situação do item nem indicar necessidade de reposição. Caso tenha outro código ou queira consultar a lista de produtos/categorias, estou à disposição.

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

## Cenário 3 — Comportamento alternativo — pergunta conceitual sem chamar API (Obrigatório)

- **Entrada:** `O que significa estoque mínimo na gestão de inventário?`
- **Resultado esperado:** Responder diretamente pela transição condicional do LangGraph SEM chamar nenhuma ferramenta nem consultar a API (ferramentas_chamadas == []).
- **Status da validação:** **PASSOU**
- **Iterações no LangGraph:** `1`
- **Ferramentas acionadas:** `nenhuma`

### Resposta observada do agente

**Estoque mínimo** (ou *estoque de segurança*) é a quantidade mínima de um item que a empresa decide manter em seu depósito para garantir que a demanda dos clientes seja atendida mesmo diante de imprevistos, como atrasos na reposição, variações inesperadas na demanda ou falhas na produção.

### Por que ele é importante?
1. **Evita rupturas (stock‑outs)** – Quando o nível de estoque cai abaixo do mínimo, há risco de não conseguir atender pedidos, o que pode gerar perda de vendas e insatisfação do cliente.  
2. **Mantém a operação fluindo** – Em processos de produção ou prestação de serviços, o estoque mínimo assegura que os insumos críticos estejam sempre disponíveis.  
3. **Equilibra custos** – Manter um estoque muito alto gera custos de armazenagem, capital parado e risco de obsolescência. O estoque mínimo busca o ponto de equilíbrio entre disponibilidade e custo.

### Como ele é definido?
- **Análise de demanda**: histórico de consumo, sazonalidade e previsões de vendas.  
- **Tempo de reposição (lead time)**: quanto tempo leva para receber um novo lote após o pedido.  
- **Variabilidade**: flutuações tanto na demanda quanto no lead time são consideradas para adicionar uma margem de segurança.  
- **Política da empresa**: nível de serviço desejado (por exemplo, 95 % de atendimento sem falta) influencia o cálculo.

### Fórmula simplificada (para itens com demanda constante)
\[
\text{Estoque Mínimo} = \text{Consumo Médio Diário} \times \text{Lead Time} + \text{Margem de Segurança}
\]

- **Consumo Médio Diário**: quantidade média consumida por dia.  
- **Lead Time**: número de dias entre o pedido e a chegada do item.  
- **Margem de Segurança**: estoque extra para cobrir variações inesperadas (geralmente calculada a partir do desvio‑padrão da demanda ou do lead time).

### Exemplos de uso
- **Produtos de alta rotatividade**: podem ter um estoque mínimo maior para evitar rupturas frequentes.  
- **Itens caros ou de baixa demanda**: podem ter um estoque mínimo mais baixo, reduzindo o capital imobilizado.  

Em resumo, o estoque mínimo é um parâmetro estratégico que ajuda a equilibrar a disponibilidade de produtos com os custos de manutenção de inventário, garantindo que a empresa possa atender seus clientes de forma confiável e eficiente.

### Evidência técnica (logs de ferramentas e n8n)

```json
{
  "ferramentas_chamadas": [],
  "resultados_tools": [],
  "alertas_n8n": []
}
```

## Cenário 4 — Indisponibilidade simulada da API — HTTP 503 (Bônus de confiabilidade)

- **Entrada:** `Consulte o produto PRD-503.`
- **Resultado esperado:** Chamar consultar_produto com PRD-503, tratar o erro HTTP 503 (servico_indisponivel) e avisar o usuário de forma controlada sem inventar dados.
- **Status da validação:** **PASSOU**
- **Iterações no LangGraph:** `2`
- **Ferramentas acionadas:** `consultar_produto`

### Resposta observada do agente

Desculpe, mas o serviço de consulta ao estoque está temporariamente indisponível no momento. Não foi possível obter os dados do produto **PRD-503**. Por favor, tente novamente mais tarde ou, se preferir, informe outro código ou categoria que eu possa consultar quando o serviço estiver ativo.

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

## Cenário 5 — Validação de código em formato inválido — ABC-1 (Bônus de segurança)

- **Entrada:** `Qual o estoque do código ABC-1?`
- **Resultado esperado:** Rejeitar o parâmetro fora do padrão PRD-XXX (validação local na tool ou orientação direta do agente) e orientar o usuário sobre o formato correto sem inventar dados.
- **Status da validação:** **PASSOU**
- **Iterações no LangGraph:** `2`
- **Ferramentas acionadas:** `consultar_produto`

### Resposta observada do agente

O código **ABC-1** não está no formato aceito pela API de estoque.  
Os códigos válidos devem seguir o padrão **PRD-XXX**, onde **XXX** são três dígitos (ex.: PRD-001).  

Por isso, não foi possível localizar o produto. Se desejar consultar um item, informe o código correto no formato indicado.

### Evidência técnica (logs de ferramentas e n8n)

```json
{
  "ferramentas_chamadas": [
    {
      "nome": "consultar_produto",
      "args": {
        "codigo": "ABC-1"
      }
    }
  ],
  "resultados_tools": [
    {
      "tool": "consultar_produto",
      "conteudo": "{\"sucesso\": false, \"erro\": \"codigo_invalido\", \"mensagem\": \"Código 'ABC-1' inválido. Informe no padrão PRD-XXX (três dígitos, exemplo: PRD-001).\"}"
    }
  ],
  "alertas_n8n": []
}
```
