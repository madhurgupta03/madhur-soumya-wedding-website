# AGENTS.md

Instructions for any AI coding agent (Codex, ChatGPT, Claude, others).

`CLAUDE.md` is the single source of truth for this project. Read it first, then `SETUP.md`, then `Guides/PROJECT-HISTORY.md`. Its rules apply to you whatever your name is.

Essentials:

- `Website/index.html` is generated. Never hand-edit it. Edit `Source/pipeline/build.py`, then run `python3 Source/make.py build` and `python3 Source/make.py check`.
- Dev server with hot reload: `python3 serve.py` (`http://localhost:8000`).
- Deploy the `Website/` folder as-is (Vercel).
