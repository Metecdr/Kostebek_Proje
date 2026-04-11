## graphify

This project has a graphify knowledge graph at graphify-out/.

Rules:
- Before answering architecture or codebase questions, read graphify-out/GRAPH_REPORT.md for god nodes and community structure
- If graphify-out/wiki/index.md exists, navigate it instead of reading raw files
- After modifying code files in this session, run `python3 -c "from graphify.watch import _rebuild_code; from pathlib import Path; _rebuild_code(Path('.'))"` to keep the graph current

## Context Navigation
When you need to understand codebase, docs, or any files in this project:
1. ALWAYS query the knowledge graph first: use the MCP tool `graphify_kostebek` (automatically available in cowork)
   - `query_graph("your question")` — BFS/DFS traversal
   - `shortest_path("Node A", "Node B")` — trace connections
   - `get_node("concept_name")` — detailed info
   - `god_nodes()` — most connected concepts
2. Only read raw files if explicitly told "read the file" or "look at the raw file"
3. Use `graphify-out/GRAPH_REPORT.md` for god nodes, surprising connections, suggested questions
4. For wiki navigation: `graphify-out/wiki/index.md` (run `/graphify . --wiki` to regenerate)

## MCP Setup
Graph is exposed via MCP server in `~/.claude/plugins/settings.json`:
- Server: `graphify_kostebek`
- Tools: `query_graph`, `get_node`, `get_neighbors`, `get_community`, `god_nodes`, `graph_stats`, `shortest_path`
- No setup needed — automatically available in cowork chat

## Auto-Update Setup
Graph automatically updates on:
1. **Git commits** — post-commit hook installed (every `git commit` rebuilds code changes)
2. **File changes** — optionally run in terminal to auto-rebuild on doc/image changes:
   ```bash
   python -m graphify.watch . --debounce 3
   ```
3. **Manual update** — after adding notes to `raw/`:
   ```bash
   /graphify . --update
   ```

## Workflow
1. Create or modify code → `git commit` → graph auto-updates
2. Add notes to `raw/*.md` → save file → `/graphify . --update`
3. Cowork chat automatically sees latest graph via MCP
