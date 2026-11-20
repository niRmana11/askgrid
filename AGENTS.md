# AskGrid — Repository Engineering Rules

Master context lives in the sibling private folder: `../AskGrid_Context/AskGrid_Project_Context.md`

## Non-Negotiable Rules
- **Hands-on learning mode:** Do not directly modify code files in this repo unless explicitly asked; explain What, Why, How, and Where so the founder writes the code.
- **No LLM math / no `exec()`:** LLM outputs a strict Pydantic `AnalysisIntent` JSON only; deterministic Python/Pandas executes allowlisted operations.
- **Schema-only prompts:** Never send raw dataset rows to an LLM. Treat column names as untrusted input.
- **Zero secrets in git:** Use `.env` (gitignored) and keep `.env.example` updated.
- **Log metadata only:** Never log CSV cell values or PII.
- **Tests required:** Every feature or bug fix requires automated tests (`pytest` / `vitest`) and clean lint/type checks.