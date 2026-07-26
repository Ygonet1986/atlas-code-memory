# Why Atlas

## One-liner

**Atlas is the GPS for AI coding — not another chatbot memory.**

## Pitch

If you build software with Cursor, Claude Code, or Codex, you already know the loop:

1. Open a new chat  
2. Re-explain the architecture  
3. Watch the agent grep the wrong half of the monorepo  
4. Correct it  
5. Lose the correction when the thread ends  

Atlas breaks that loop with a **mandatory, portable protocol**:

```text
memory map → decisions → code graph → file index
```

You keep your editor and your models. You gain a shared orientation layer that works the same on every project.

## Migrate if…

- You maintain more than one serious repo with an AI assistant  
- Architecture decisions keep getting rediscovered  
- You installed MemPalace / Graphify / Mind Map and need **one order**, not three  
- Token spend on “exploration” hurts more than generation  

## Don’t migrate yet if…

- The project is disposable and fits in one context window  
- You have no recurring decisions to remember  

Starting early still helps: `atlas init` is cheap and grows with the repo.

## Proof points

- Local-first, MIT, no required cloud  
- Secret scanning on checkpoints  
- Scoped graphs for large codebases  
- `atlas migrate` / `atlas onboard` for adoption  
- MCP tools for agents that speak tool-calling  
