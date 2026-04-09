# NL-to-Query AI Agent — Design Spec

**Date:** 2026-04-09
**Status:** Approved
**Branch:** `feature/nl-query-agent`

## Purpose

An AI-powered natural language query assistant embedded in the existing Data Explorer (`data-explorer.html`). Users type questions in plain English; the agent clarifies ambiguity, generates SQL, validates it, and populates the explorer's controls for the user to review and execute. Built on Vercel AI SDK with Claude Opus 4.6 via the Vercel AI Gateway.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│  data-explorer.html                                      │
│  ┌──────────────────┐  ┌──────────────────────────────┐ │
│  │  Chat Sidebar     │  │  Explorer (existing)         │ │
│  │                   │  │                              │ │
│  │  [User message]   │  │  Scope / Metrics / Filters   │ │
│  │  [Agent reply]    │  │  Results Table               │ │
│  │  [User refines]   │  │  SQL Panel                   │ │
│  │  [Agent clarifies]│  │  Export Button               │ │
│  │                   │  │                              │ │
│  │  [ Type here... ] │  │  <- Agent populates these    │ │
│  └──────────────────┘  └──────────────────────────────┘ │
└──────────────┬──────────────────────────┬───────────────┘
               │ POST /api/chat           │ POST /api/query
               ▼                          ▼
┌──────────────────────┐   ┌──────────────────────────┐
│  web/api/chat.ts     │   │  web/api/query.py        │
│  (Node.js, AI SDK)   │   │  (Python, existing)      │
│                      │   │                          │
│  ToolLoopAgent       │   │  Executes SQL against    │
│  - Claude Opus 4.6   │   │  Neon PostgreSQL         │
│  - Tools:            │   └──────────────────────────┘
│    - clarify         │
│    - generate_query  │
│    - lookup_schema   │
│    - validate_sql ───┼──> calls /api/query (dry run)
└──────────────────────┘
```

### Key Architectural Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Deployment model | Embedded in Data Explorer | Leverage existing results table, SQL panel, export controls |
| Interaction model | Chat sidebar (left panel, collapsible) | Multi-turn history visible, explorer updates alongside |
| Ambiguity handling | Always clarify before executing | Matches "feedback, clarification, refinement" philosophy |
| Execution model | Agent populates, user runs | Builds trust; user reviews SQL before hitting the database |
| Query scope | Full database breadth (all tables/views) | Agent's value is making the full schema accessible |
| Auth | None (open access) | Same as existing explorer; rate limiting a future concern |
| Model | Claude Opus 4.6 via Vercel AI Gateway | Single API key, no separate Anthropic SDK |
| Frontend | Vanilla JS (no React) | Matches existing explorer, avoids framework dependency |

## Agent Tools

### `clarify`

Ask the user a clarifying question before generating SQL.

- **When called:** Ambiguous question, multiple valid interpretations, missing scope info
- **Input:** `{ question: string, options?: string[] }`
- **Output:** Rendered as chat message with optional clickable buttons for each option
- **Frontend behavior:** Buttons send the clicked option as the user's next message

### `lookup_schema`

Retrieve metadata about tables, columns, or domain values on demand.

- **When called:** Agent needs column-level detail not in the system prompt overview
- **Input:** `{ query: string }` (e.g., "compensation columns", "designation codes")
- **Output:** `{ tables: [...], columns: [...], notes: string }`
- **Implementation:** Keyword search over `web/lib/schema-index.json` (no database call)

### `generate_query`

Produce the SQL and explorer field mappings for user review.

- **When called:** After clarification is complete, agent is confident about the query
- **Input:**
  ```typescript
  {
    sql: string,              // Full SELECT query
    explanation: string,      // Plain English description
    explorer_state?: {        // Optional mapping to explorer controls
      scope?: { province?, designation?, category? },
      metrics?: string[],     // metric IDs from explorer catalog
      filters?: Array<{ column, operator, value }>,
      sort?: { column, direction },
      limit?: number
    }
  }
  ```
- **Frontend behavior:**
  - Renders explanation + "Review & Run" prompt in sidebar
  - Populates explorer scope/metric/filter controls from `explorer_state`
  - Injects raw SQL into the SQL panel
  - Highlights "Run Query" button
  - Does NOT auto-execute

### `validate_sql`

Dry-run the SQL to catch errors before presenting to user.

- **When called:** Internally after `generate_query`, before presenting to user
- **Input:** `{ sql: string }`
- **Output:** `{ valid: boolean, error?: string, row_count_estimate?: number }`
- **Implementation:** Calls existing `/api/query` with `LIMIT 0` appended
- **On failure:** Agent self-corrects (up to 2 retries), may call `lookup_schema` to fix column references
- **Frontend behavior:** Not rendered in sidebar (internal plumbing)

## System Prompt Strategy

The system prompt is kept lean. Full column-level detail is available on demand via `lookup_schema`.

### System Prompt Contents

1. **Role & behavior** — "You are a data query assistant for the Canadian Registered Charities database (CRA T3010 filings, ~83,000 charities). Always clarify ambiguous questions before generating SQL. Never execute queries directly — generate them for user review."

2. **Schema overview (~500 tokens)** — Table names, row counts, purpose, join relationships:
   - Core: `charity_base` (master), `latest_filing`, `charity_counts`
   - Financial: `financial_d` (balance sheet/income), `financial_abc` (programs/Y-N/DAF)
   - Schedules: `schedule_1` through `schedule_8` (foundations, foreign ops, compensation, non-cash, disbursement)
   - Detail: `programs`, `grants`, `trustee`
   - Lookups: `lookup_designation`, `lookup_category`, `lookup_country`, `lookup_province`, `lookup_programs`
   - Views: `v_financial_d`, `v_financial_abc`, `v_compensation`, `v_programs`, `v_grants`, `v_foreign_recipients`, `v_operating_countries`, `v_subsidiaries`

3. **Critical quirks:**
   - Currency fields are VARCHAR (`"$1,234,567"`) — prefer views (`v_financial_d`, etc.) which pre-convert these. If querying raw tables, use `CAST(REPLACE(REPLACE(col,'$',''),',','') AS DECIMAL)` (PostgreSQL-safe). Wrap in a CASE/NULLIF to handle non-numeric values gracefully.
   - BN column name varies: `"BN/Registration Number"` (capital N) in `ident`, `financial_d`, `schedule_8_disbursement`; `"BN/Registration number"` (lowercase n) elsewhere; `bn` in `charity_base` and views
   - Always LEFT JOIN from `charity_base`
   - Designation codes: A=Public Foundation, B=Private Foundation, C=Charitable Organization
   - Schedule 3 mixed types: lines 300/370 are BIGINT, line 390 is VARCHAR
   - Form version changes (V23 to V24): lines 4575, 4580, 4101, 4102 changed meaning — flag when user asks about these
   - Line 4570 (total government funding) is unreliable — compute as 4540+4550+4560

4. **Prefer views** — Use `v_financial_d`, `v_compensation`, etc. when they cover the needed columns. Fall back to raw tables only when views don't expose the required fields.

5. **Target dialect** — Generate PostgreSQL-compatible SQL (Neon PostgreSQL in production). Use `TRY_CAST` for DuckDB compatibility note in validation.

### Example Q&A Pairs (in system prompt)

6 examples demonstrating the clarify → generate pattern:

1. **Single charity lookup:** "What's the total revenue of charity 119080464RR0001?" → `v_financial_d` query, no clarification needed
2. **Scoped ranking:** "Show me the 20 largest public foundations by assets" → `designation_code = 'A'`, ORDER BY total_assets DESC, LIMIT 20
3. **Counting with joins:** "How many charities in BC have foreign operations?" → COUNT DISTINCT on `schedule_2_countries` joined to `charity_base` WHERE province = 'BC'
4. **Comparative aggregation:** "What percentage of charities spend more on fundraising than programs?" → Clarify: "across all charities, or within a specific province/designation?" → Comparison of lines 5020 vs 5000
5. **Multi-table with amount filter:** "List charities that gave grants over $100,000 to recipients in Africa" → JOIN `v_grants` + `lookup_country`, WHERE on amount + continent
6. **Category + province scoping:** "Show compensation breakdown for hospitals in Ontario" → Clarify: "by salary bands or just totals?" → `v_compensation` scoped to category + province

## Schema Index

### Structure (`web/lib/schema-index.json`)

```json
{
  "tables": {
    "<table_name>": {
      "description": "string",
      "rows": "number",
      "pk": "string (if applicable)",
      "bn_column": "string (exact BN column name for this table)",
      "columns": {
        "<column_name>": {
          "type": "string",
          "description": "string",
          "line": "string (T3010 line number, if applicable)",
          "convert": "boolean (true if currency VARCHAR needing TRY_CAST)"
        }
      },
      "quirks": ["string[]"]
    }
  },
  "views": {
    "<view_name>": {
      "description": "string",
      "source_table": "string",
      "columns": {
        "<column_name>": {
          "source": "string (table.column it maps from)",
          "type": "string",
          "pre_converted": "boolean"
        }
      }
    }
  },
  "joins": {
    "<table_a> -> <table_b>": "join condition string"
  },
  "domain_values": {
    "<column_name>": { "<code>": "label" }
  }
}
```

### Build Process

`scripts/build_schema_index.py` introspects the DuckDB database:
- Reads all table/view names and column metadata via `INFORMATION_SCHEMA`
- Enriches with T3010 line mappings from `CRA_T3010_Reference.md`
- Enriches with quirk notes from `CLAUDE.md`
- Outputs to `web/lib/schema-index.json`
- Run once, commit output. Rebuild when schema changes.

### Lookup Behavior

The `lookup_schema` tool searches the index via keyword matching across table names, column names, descriptions, and T3010 line numbers. Returns the matching subset with all metadata.

## Frontend Integration

### Sidebar

- **Position:** Left side, collapsible via toggle button
- **Width:** ~320px when open; explorer shifts right
- **Toggle:** Button always visible in top-left corner (collapsed state shows an "AI" icon)
- **Scrollable:** Independent scroll from the explorer panel

### Message Rendering

| Message type | Rendering |
|---|---|
| User text | Right-aligned bubble, user's typed message |
| Agent text | Left-aligned, markdown-capable (for lists, bold, code) |
| `tool-clarify` | Question text + option buttons (if `options` provided) |
| `tool-generate_query` | Explanation + "Review & Run" button; triggers explorer population |
| `tool-lookup_schema` | Not rendered (internal) |
| `tool-validate_sql` | Not rendered (internal) |
| Error | Error message + "Retry" button |
| Streaming | Typing indicator while agent is thinking |

### Stream Consumption (Vanilla JS)

```javascript
const response = await fetch('/api/chat', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ messages })
});

const reader = response.body.getReader();
const decoder = new TextDecoder();

while (true) {
  const { done, value } = await reader.read();
  if (done) break;
  const chunk = decoder.decode(value);
  // Parse UI message stream chunks, update sidebar DOM
}
```

### Explorer Integration

When `generate_query` fires with an `explorer_state`:
- Scope dropdowns set to matching province/designation/category
- Metric checkboxes toggled for listed metric IDs
- Filter rows created for each filter entry
- Sort dropdown and direction set
- Limit slider adjusted
- SQL panel populated with raw SQL
- "Run Query" button highlighted (pulsing border or color change)

## Error Handling & Safety

### Query Safety Layers

1. **System prompt:** "Only generate SELECT statements"
2. **`validate_sql`:** Pre-execution dry run catches syntax errors and invalid references
3. **Existing `/api/query` enforcement:** SELECT-only (rejects DDL/DML)

### Agent Loop Guardrails

- **Step limit:** `stopWhen: stepCountIs(8)` — typical flow is 2-4 steps
- **Self-correction:** On `validate_sql` failure, agent retries up to 2 times (calling `lookup_schema` to fix column references)
- **Out-of-scope questions:** Agent responds: "I can only help with questions about Canadian registered charities data."
- **Zero results:** Agent notes this and suggests broadening filters

### Graceful Degradation

- If AI Gateway is unavailable: sidebar shows "AI assistant temporarily unavailable" — explorer remains fully functional
- If stream is interrupted: partial response shown + retry button
- If agent hits step limit: shows what it has so far + suggestion to simplify the question

## File Structure

### New Files

```
web/
├── api/
│   └── chat.ts                    # AI SDK agent endpoint (Node.js)
├── lib/
│   ├── agents/
│   │   └── query-agent.ts         # ToolLoopAgent definition + type export
│   ├── tools/
│   │   ├── clarify.ts             # clarify tool
│   │   ├── generate-query.ts      # generate_query tool
│   │   ├── lookup-schema.ts       # lookup_schema tool
│   │   └── validate-sql.ts        # validate_sql tool
│   └── schema-index.json          # Pre-built schema metadata
├── package.json                   # ai, zod dependencies
└── tsconfig.json                  # TypeScript config

scripts/
└── build_schema_index.py          # Schema index generator
```

### Modified Files

```
web/vercel.json                    # Add /api/chat route for Node.js
web/public/index.html              # Add chat sidebar HTML/CSS/JS
data-explorer.html                 # Add chat sidebar HTML/CSS/JS (source of truth)
.gitignore                         # Add web/node_modules/
```

### Dependencies

```json
{
  "dependencies": {
    "ai": "^6.0.34",
    "zod": "^3.23.0"
  }
}
```

### Environment Variables

| Variable | Where | Purpose |
|---|---|---|
| `AI_GATEWAY_API_KEY` | Vercel (new) | Vercel AI Gateway authentication |
| `NEON_DATABASE_URL` | Vercel (existing) | PostgreSQL connection for query execution |

### Local Development

Use `vercel dev` for the full multi-runtime experience (Node.js chat endpoint + Python query endpoints). `AI_GATEWAY_API_KEY` in `.env.local`.

## Dialect Note

The production database is **Neon PostgreSQL**. The local database is **DuckDB**. Key differences:
- `TRY_CAST` is DuckDB-specific; PostgreSQL uses `CAST` (which throws on invalid input) or a custom safe-cast function
- The existing views (`v_financial_d`, etc.) handle conversion at the view level, making this largely transparent
- The agent should generate PostgreSQL-compatible SQL for production. The `validate_sql` tool validates against the production database.
