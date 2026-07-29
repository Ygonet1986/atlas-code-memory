# O GPS que falta aos agentes de IA

*Como o Atlas Memory corta o custo de explorar monorepos — e deixa o modelo fazer o que sabe fazer melhor: gerar código.*

---

Abra um chat novo no Cursor, no Claude Code ou em qualquer editor com agente. O modelo é o mesmo de ontem. O repositório também. Mesmo assim, a conversa começa do zero.

Ele não lembra que a equipe escolheu Postgres no mês passado. Não sabe qual pasta do monorepo importa para autenticação. Grepa metade da árvore, lê arquivos errados, gasta tokens — e ainda pode contradizer a decisão da semana anterior, porque aquela conversa morreu com o thread.

**O gargalo não é o modelo. É a orientação.**

É exatamente esse problema que o **Atlas Memory** ataca: não inventar mais um “cérebro” para a IA, e sim um **roteador local e determinístico** que diz *onde olhar* antes de gastar contexto.

---

## Uma metáfora que cabe no bolso

Pense no GPS do carro.

Você não espera que o navegador memorize cada rua do país na sua cabeça. Você espera que ele: (1) saiba o mapa, (2) entenda o destino, (3) escolha uma rota curta, (4) atualize se a via estiver fechada.

Agentes de código, hoje, muitas vezes fazem o equivalente a dirigir sem mapa: saem greppando o continente inteiro.

O Atlas é o GPS. O modelo continua sendo o motorista.

> **Atlas em uma frase:** GPS local para coding com IA — entende o projeto, desambigua o arquivo certo, grava a memória útil e reduz tokens de exploração.

---

## O que ele é (e o que não é)

| Atlas é | Atlas não é |
|---------|-------------|
| Um **protocolo fixo** de busca (a *Atlas Walk*) | Mais um chatbot |
| Um **roteador** sobre índices e memórias | Um substituto do Cursor/Claude |
| **Local-first**, MIT, sem nuvem obrigatória | Um banco vetorial obrigatório |
| Compatível com MemPalace, Graphify ou Mind Map | “Mais uma ferramenta brigando para ser a primeira” |

Ele não substitui RAG, git ou a janela de contexto do modelo. Ele define a **ordem de consulta**. Com a mesma pergunta e o mesmo estado do projeto, o caminho é o mesmo. Determinismo é o ponto.

---

## A caminhada de cinco camadas

Toda pergunta séria passa pela mesma sequência. Camada ausente? Pula. Acerto? Para. Nunca inventa memória.

```
pergunta
   → índice de memória (qual “ala” / sala?)
   → provedor de memória (o que decidimos?)
   → índice de grafo (qual escopo de código?)
   → grafo (como se conecta?)
   → project-cache (qual arquivo abrir?)
```

Na prática, o dia a dia do desenvolvedor vira:

1. **Entender** o projeto pelos índices (sem dump do repo).  
2. **Desambiguar** com `atlas route` / MCP — poucos arquivos certos.  
3. **Lembrar** decisões em *drawers* tipados (arquitetura, bugfix, preferência…).  
4. **Economizar** na próxima sessão, porque o agente não reexplora o monorepo às cegas.

O código sempre vence memória velha: se o repo mudou, a memória marca *stale* ou *superseded*. Segredos não entram nos drawers — há varredura no checkpoint.

---

## O argumento econômico: tokens

Em monorepo grande, o custo caro raramente é a resposta final. É a **exploração**: grep cego, dezenas de arquivos irrelevantes no contexto, correções em cascata.

O Atlas traz um harness mensurável:

```bash
atlas bench --fixture
```

No fixture sintético (centenas de arquivos-isca + índices corretos), o braço “grep cego” e o braço “rota Atlas” são comparados com um *proxy* determinístico de tokens (`caracteres ÷ 4`). No ambiente de desenvolvimento atual, o fixture reporta da ordem de **~99% de redução** no material que entraria no contexto — o agente ainda encontra o arquivo certo (`login.py`, `invoice.py`, etc.).

Não é fatura da OpenAI. É prova auditável de que **orientação bem feita** reduz o que o modelo precisa ler. Em projeto real: `atlas bench -C /seu/monorepo` com o `project-cache` preenchido.

---

## Memória de projeto e memória de vida

Há dois “palácios”:

**Projeto** — decisões de arquitetura, lições de debug, convenções. Índices em `.cursor/`, drawers por sala (`architecture`, `debugging`, `build`…).

**Life** — memória pessoal entre conversas e projetos: dia, semana, mês, ano; pessoas e entidades; sync com GitHub privado. O agente “acorda” com `atlas life wake`, grava com `remember`, retoma com *session init*.

Para quem usa o desktop, o **Atlas Chat** (Vite + Tauri) fala com o mesmo núcleo: chat com DeepSeek, mapa mental, entidades — e agora a aba **Savings**, que dispara o bench.

---

## Um app local para qualquer editor de IA

A ideia de produto amadureceu: uma instalação, vários clientes.

```bash
atlas daemon          # HTTP em 127.0.0.1:8765
atlas connect --editor cursor   # ou claude | generic
atlas-mcp             # MCP via stdio
```

Cursor, Claude Code, Windsurf ou um editor genérico consomem o mesmo daemon. O Atlas Chat sobe o serviço e mostra status; o editor continua sendo onde você programa.

É o caminho para “instale uma vez, use em qualquer IDE com agente”.

---

## Como começa na prática

```bash
pip install -e .          # ou do PyPI: atlas-memory
cd ~/code/meu-app
atlas init --global-rule
atlas onboard
atlas doctor
atlas connect --editor cursor
atlas bench --fixture     # ver a prova de economia
```

No Cursor, a regra global e o MCP `atlas-mcp` empurram o agente a **rotear antes de grepar**. Depois de uma feature importante: um *checkpoint* drawer. Depois de uma conversa longa: `session-end` no Life.

---

## Para quem vale a pena

**Vale** se você:

- mantém mais de um repositório sério com assistente de IA;  
- já repetiu “a gente tinha decidido X” mais de duas vezes;  
- sente o monorepo engolir a janela de contexto;  
- instalou MemPalace / Graphify / Mind Map e quer **uma hierarquia**, não três regras competindo.

**Pode esperar** se o projeto cabe num único contexto e não há decisões recorrentes — embora `atlas init` seja barato e cresça com o repo.

---

## O quadro maior

A indústria de coding com IA otimizou geração: modelos maiores, ferramentas melhores, prompts mais longos. Poucos otimizaram **orientação**.

Sem orientação, cada chat é um onboarding caro. Com orientação, o modelo recebe um mapa curto, arquivos certos e a memória que importa — e gasta tokens onde gera valor.

O Atlas Memory não promete pensar por você. Promete que o agente **saiba onde está** — no projeto, na decisão da semana passada e, se quiser, na sua vida digital — sem reabrir o continente inteiro a cada mensagem.

GPS ligado. Agora dirija.

---

*Atlas Memory é software livre (MIT). Documentação: `docs/` no repositório. Prova de tokens: `atlas bench`. Daemon local: `atlas daemon`.*
