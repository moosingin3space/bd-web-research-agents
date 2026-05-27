# Bright Data Web Research Agent

A minimal OpenAI Agents SDK example for a deep-research agent that uses Bright Data APIs for deterministic web search and page fetching.

The demo asks a company/product/market question, searches the web, reads source pages, and returns schema-validated JSON with citations.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
cp .env.example .env
```

Fill in `.env`:

```bash
OPENAI_API_KEY=...
BRIGHT_DATA_API_TOKEN=...
BRIGHT_DATA_SERP_ZONE=serp_api1
BRIGHT_DATA_UNLOCKER_ZONE=web_unlocker1
```

## Run

```bash
python -m bright_research_agent.agent \
  "What is the market positioning of Perplexity's enterprise search product?"
```

Progress and tool-call logs are written to stderr so stdout remains valid JSON:

```bash
python -m bright_research_agent.agent \
  "What is the market positioning of Perplexity's enterprise search product?" \
  --log-level INFO
```

Set `--log-level WARNING` or `LOG_LEVEL=WARNING` for quieter output.

If the OpenAI request times out, give the model call more room and reduce turns:

```bash
python -m bright_research_agent.agent \
  "What is the current landscape of GTM engineering?" \
  --openai-timeout 300 \
  --max-turns 6
```

The final output is JSON matching the Pydantic schema in `src/bright_research_agent/schemas.py`.

## Movements Discovery

A second entry point runs a discovery workflow across a fixed watchlist of AI labs
and startups (OpenAI, Anthropic, xAI, Perplexity, Cursor, Mistral, Cognition).
It surfaces notable movements (personnel, product, funding, M&A, research,
org change, partnership, regulatory) over three nested recency buckets
(`breaking` 7d / `recent` 30d / `context` 90d) and emits a Markdown report.

```bash
python -m bright_research_agent.movements \
    --watchlist config/watchlist.yaml
```

Useful flags:

```bash
python -m bright_research_agent.movements \
    --watchlist config/watchlist.yaml \
    --format json \
    --out reports/2026-05-26.json \
    --concurrency 3 \
    --log-level INFO
```

The watchlist roster and the source-bias allowlist (news + LinkedIn) live in
`config/watchlist.yaml`. Each org has `aliases` (broadens the SERP query) and
`domains` (reserved for future first-party-source boosting). Editing the
roster is a config change, not a code change.

## What This Demonstrates

- SERP discovery through Bright Data SERP API.
- Page retrieval through Bright Data Unlocker API.
- OpenAI Agents SDK tool orchestration.
- Pydantic output validation for citation-backed research JSON.

## Notes

- Treat scraped content as untrusted input. The agent instructions explicitly tell the model not to follow instructions found inside retrieved pages.
- Keep `max_sources` low during demos so the workflow stays fast and inexpensive.
- This API-first version is the clearest starting point for retries, concurrency, metrics, and cost controls.
