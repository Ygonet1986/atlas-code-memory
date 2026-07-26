# Graphify Index

Camada 3 do **Atlas**. Meta-mapa dos grafos escopados.
**Não** é AI Mind Map. Consulta por busca; nunca ler inteiro.
Statuses: `ready` | `missing` | `stale` — use `atlas stale`.

## Como usar

1. Buscar escopo.
2. Se `ready` → query no grafo daquele escopo.
3. Se `stale`/`missing` → atualizar/criar, depois este índice.

## Formato

```markdown
### <nome-curto>
- **escopo:** `<caminho/relativo>`
- **grafo:** `<caminho>/graphify-out/`
- **descrição:** <1–3 frases>
- **status:** ready | missing | stale
```

## Escopos

<!-- Um escopo = um grafo. Evite graphify na raiz de monorepos enormes. -->

_Nenhum Graphify registrado ainda._
