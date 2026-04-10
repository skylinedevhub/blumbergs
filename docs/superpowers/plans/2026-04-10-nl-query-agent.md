# NL-to-Query AI Agent Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a natural language query assistant chat sidebar to the Data Explorer, powered by Claude Opus 4.6 via Vercel AI SDK, that clarifies ambiguous questions and generates SQL for user review.

**Architecture:** A Node.js serverless function (`web/api/chat.ts`) uses `streamText` from the AI SDK with 2 tools (`lookup_schema`, `generate_query`) and Claude Opus 4.6 via the Vercel AI Gateway. The frontend adds a collapsible chat sidebar to `data-explorer.html` that consumes the NDJSON stream, renders messages, and populates the explorer's controls when a query is generated.

**Tech Stack:** Vercel AI SDK v6 (`ai` package), Zod, TypeScript (server), vanilla JS (client), Vercel AI Gateway with `anthropic/claude-opus-4.6`

**Spec:** `docs/superpowers/specs/2026-04-09-nl-query-agent-design.md`

---

### Task 1: Node.js Project Scaffolding

**Files:**
- Create: `web/package.json`
- Create: `web/tsconfig.json`
- Create: `web/.gitignore`

- [ ] **Step 1: Create package.json**

Write to `web/package.json`:

```json
{
  "name": "blumbergs-data-explorer",
  "private": true,
  "type": "module",
  "dependencies": {
    "ai": "^6.0.34",
    "zod": "^3.23.0"
  }
}
```

- [ ] **Step 2: Create tsconfig.json**

Write to `web/tsconfig.json`:

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ES2022",
    "moduleResolution": "bundler",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "resolveJsonModule": true,
    "outDir": "dist",
    "rootDir": ".",
    "baseUrl": ".",
    "paths": {
      "@/*": ["./*"]
    }
  },
  "include": ["api/**/*.ts", "lib/**/*.ts"],
  "exclude": ["node_modules", "dist"]
}
```

- [ ] **Step 3: Create web/.gitignore**

Write to `web/.gitignore`:

```
node_modules/
dist/
.env.local
```

- [ ] **Step 4: Install dependencies**

```bash
cd /home/user/blumbergs-main/.worktrees/nl-query-agent/web && npm install
```

Expected: `node_modules/` created with `ai` and `zod` packages.

- [ ] **Step 5: Verify TypeScript config is valid**

```bash
cd /home/user/blumbergs-main/.worktrees/nl-query-agent/web && npx tsc --noEmit
```

Expected: No errors (no .ts files yet).

- [ ] **Step 6: Commit scaffolding**

```bash
cd /home/user/blumbergs-main/.worktrees/nl-query-agent
git add web/package.json web/tsconfig.json web/.gitignore web/package-lock.json
git commit -m "chore: add Node.js scaffolding for AI agent endpoint"
```

---

### Task 2: Schema Index Builder

**Files:**
- Create: `scripts/build_schema_index.py`
- Create: `web/lib/schema-index.json` (generated output)

This script introspects the DuckDB database and builds a JSON index of all tables, views, columns, types, descriptions, join conditions, and domain values.

- [ ] **Step 1: Write the schema index builder**

Create `scripts/build_schema_index.py` with:

- T3010 line number descriptions dict (all ~180 lines from the data-explorer field catalog)
- BN column name mapping per table
- JOIN condition mapping to charity_base
- `build_index()` function that:
  - Connects to `data/db/cra_charities.duckdb` read-only
  - Queries `information_schema.tables` and `information_schema.columns` for all tables and views
  - Enriches columns with T3010 line descriptions, currency flags
  - Reads domain values from lookup tables
  - Adds quirks array (currency format, BN column variations, SQL dialect notes)
  - Writes JSON to `web/lib/schema-index.json`

The full script content is in the spec appendix. Key structures in the output JSON:

```
{
  "tables": { "<name>": { "description", "rows", "bn_column", "join_to_charity_base", "columns": { "<col>": { "type", "description?", "line?", "currency?" } } } },
  "views": { "<name>": { "description", "columns": { ... } } },
  "joins": { "<table>": "<join condition>" },
  "domain_values": { "lookup_designation": { "A": "Public Foundation", ... }, ... },
  "quirks": [ "Currency fields are VARCHAR...", ... ]
}
```

- [ ] **Step 2: Run the builder from the main repo (has the DuckDB database)**

```bash
cd /home/user/blumbergs-main && python3 scripts/build_schema_index.py
```

Expected:
```
Schema index written to web/lib/schema-index.json
  Tables: ~25
  Views: ~8
  Total columns: ~500+
  Domain value sets: 5
```

- [ ] **Step 3: Verify the output structure**

```bash
cd /home/user/blumbergs-main && python3 -c "
import json
idx = json.load(open('web/lib/schema-index.json'))
print('Tables:', len(idx['tables']))
print('Views:', len(idx['views']))
print('charity_base cols sample:', list(idx['tables']['charity_base']['columns'].keys())[:5])
fd_4700 = idx['tables']['financial_d']['columns'].get('4700', {})
print('Line 4700 desc:', fd_4700.get('description', 'MISSING'))
print('Quirks count:', len(idx['quirks']))
"
```

- [ ] **Step 4: Copy schema index to worktree**

```bash
mkdir -p /home/user/blumbergs-main/.worktrees/nl-query-agent/web/lib
cp /home/user/blumbergs-main/web/lib/schema-index.json /home/user/blumbergs-main/.worktrees/nl-query-agent/web/lib/schema-index.json
```

- [ ] **Step 5: Commit**

```bash
cd /home/user/blumbergs-main/.worktrees/nl-query-agent
git add scripts/build_schema_index.py web/lib/schema-index.json
git commit -m "feat: add schema index builder and generated index for NL agent"
```

---

### Task 3: Tool Definitions

**Files:**
- Create: `web/lib/tools/lookup-schema.ts`
- Create: `web/lib/tools/generate-query.ts`

- [ ] **Step 1: Create the lookup_schema tool**

Create `web/lib/tools/lookup-schema.ts`:

```typescript
import { tool } from 'ai';
import { z } from 'zod';
import schemaIndex from '../schema-index.json' with { type: 'json' };

type ColumnInfo = { type: string; description?: string; line?: string; currency?: boolean };
type TableInfo = { description: string; rows: number; columns: Record<string, ColumnInfo>; bn_column?: string; join_to_charity_base?: string };
type ViewInfo = { description: string; columns: Record<string, ColumnInfo> };

export const lookupSchemaTool = tool({
  description:
    'Search the database schema for tables, columns, views, join conditions, or domain values. ' +
    'Use when you need column-level detail or want to find which table/column maps to a concept.',
  inputSchema: z.object({
    query: z.string().describe('Search term: table name, column name, T3010 line number, or concept'),
  }),
  execute: async ({ query }) => {
    const q = query.toLowerCase();
    const tables: Array<{ name: string; description: string; rows: number; matchedColumns: Record<string, ColumnInfo>; bn_column?: string; join?: string }> = [];
    const views: Array<{ name: string; description: string; matchedColumns: Record<string, ColumnInfo> }> = [];
    const domainValues: Record<string, Record<string, string>> = {};
    let quirks: string[] = [];

    for (const [tname, tinfo] of Object.entries(schemaIndex.tables as Record<string, TableInfo>)) {
      const nameMatch = tname.includes(q);
      const descMatch = tinfo.description.toLowerCase().includes(q);
      const matched: Record<string, ColumnInfo> = {};
      for (const [cname, cinfo] of Object.entries(tinfo.columns)) {
        if (cname.toLowerCase().includes(q) || (cinfo.description && cinfo.description.toLowerCase().includes(q)) || (cinfo.line && cinfo.line === query)) {
          matched[cname] = cinfo;
        }
      }
      if (nameMatch || descMatch || Object.keys(matched).length > 0) {
        tables.push({
          name: tname, description: tinfo.description, rows: tinfo.rows,
          matchedColumns: Object.keys(matched).length > 0 ? matched : {},
          ...(tinfo.bn_column ? { bn_column: tinfo.bn_column } : {}),
          ...(tinfo.join_to_charity_base ? { join: tinfo.join_to_charity_base } : {}),
        });
      }
    }

    for (const [vname, vinfo] of Object.entries(schemaIndex.views as Record<string, ViewInfo>)) {
      const nameMatch = vname.includes(q);
      const descMatch = vinfo.description.toLowerCase().includes(q);
      const matched: Record<string, ColumnInfo> = {};
      for (const [cname, cinfo] of Object.entries(vinfo.columns)) {
        if (cname.toLowerCase().includes(q) || (cinfo.description && cinfo.description.toLowerCase().includes(q))) {
          matched[cname] = cinfo;
        }
      }
      if (nameMatch || descMatch || Object.keys(matched).length > 0) {
        views.push({ name: vname, description: vinfo.description, matchedColumns: Object.keys(matched).length > 0 ? matched : {} });
      }
    }

    for (const [dvName, dvValues] of Object.entries(schemaIndex.domain_values as Record<string, Record<string, string>>)) {
      if (dvName.toLowerCase().includes(q)) {
        domainValues[dvName] = dvValues;
      } else {
        const matched: Record<string, string> = {};
        for (const [code, desc] of Object.entries(dvValues)) {
          if (code.toLowerCase().includes(q) || desc.toLowerCase().includes(q)) matched[code] = desc;
        }
        if (Object.keys(matched).length > 0) domainValues[dvName] = matched;
      }
    }

    quirks = (schemaIndex.quirks as string[]).filter(qk => qk.toLowerCase().includes(q));

    return { tables, views, domainValues, quirks };
  },
});
```

- [ ] **Step 2: Create the generate_query tool**

Create `web/lib/tools/generate-query.ts`:

```typescript
import { tool } from 'ai';
import { z } from 'zod';

export const generateQueryTool = tool({
  description:
    'Generate the final SQL query for user review. Validates by running with LIMIT 0. ' +
    'If validation fails, fix the SQL and call again. Include explorer_state to map to the UI.',
  inputSchema: z.object({
    sql: z.string().describe('Complete PostgreSQL-compatible SELECT query'),
    explanation: z.string().describe('Plain English description of what the query does'),
    explorer_state: z.object({
      scope: z.object({
        province: z.string().optional(),
        designation: z.string().optional(),
        category: z.string().optional(),
      }).optional(),
      metrics: z.array(z.string()).optional().describe('Explorer metric IDs, e.g. "fd_4700"'),
      filters: z.array(z.object({ column: z.string(), operator: z.string(), value: z.string() })).optional(),
      sort: z.object({ column: z.string(), direction: z.enum(['ASC', 'DESC']) }).optional(),
      limit: z.number().optional(),
    }).optional().describe('Optional mapping to Data Explorer UI controls'),
  }),
  execute: async ({ sql }) => {
    const baseUrl = process.env.VERCEL_URL
      ? `https://${process.env.VERCEL_URL}`
      : `http://localhost:${process.env.PORT || 3000}`;

    const validationSql = sql.replace(/;\s*$/, '') + ' LIMIT 0';

    try {
      const resp = await fetch(`${baseUrl}/api/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sql: validationSql }),
      });
      const data = await resp.json() as { error?: string; columns?: string[] };

      if (data.error) {
        return { valid: false, error: data.error, hint: 'Fix the SQL and call generate_query again.' };
      }
      return { valid: true, columns: data.columns, message: 'Query validated. User can now review and run it.' };
    } catch (e) {
      return { valid: false, error: `Validation request failed: ${e instanceof Error ? e.message : String(e)}`, hint: 'Present the query with a note that it could not be validated.' };
    }
  },
});
```

- [ ] **Step 3: Type-check**

```bash
cd /home/user/blumbergs-main/.worktrees/nl-query-agent/web && npx tsc --noEmit
```

Expected: No type errors.

- [ ] **Step 4: Commit**

```bash
cd /home/user/blumbergs-main/.worktrees/nl-query-agent
git add web/lib/tools/lookup-schema.ts web/lib/tools/generate-query.ts
git commit -m "feat: add lookup_schema and generate_query tools for NL agent"
```

---

### Task 4: System Prompt and Chat API Endpoint

**Files:**
- Create: `web/lib/agents/system-prompt.ts`
- Create: `web/api/chat.ts`
- Modify: `web/vercel.json`

- [ ] **Step 1: Create the system prompt module**

Create `web/lib/agents/system-prompt.ts` containing the full system prompt string. The prompt includes:

1. **Role**: "You are a data query assistant for the CRA T3010 charities database. Always clarify ambiguous questions. Never execute queries — generate them for user review."
2. **Schema overview** (~500 tokens): All table names, row counts, join relationships, and view names with their friendly column names.
3. **Critical rules**: PostgreSQL dialect, currency conversion pattern, BN column variations, designation codes, unreliable line 4570, schedule 3 mixed types, SELECT-only.
4. **Workflow**: Read question -> clarify if ambiguous (as text, no tool call) -> lookup_schema for details -> generate_query with SQL + explorer_state -> handle validation errors with retry.
5. **Explorer state mapping**: Metric ID format (`{alias}_{line}`), scope codes, filter structure.
6. **6 example Q&A pairs**: Single charity lookup, scoped ranking, counting with joins, comparative aggregation, multi-table with filter, clarification example.

Export as: `export const SYSTEM_PROMPT: string`

The full prompt text is specified in the design spec section "System Prompt Strategy".

- [ ] **Step 2: Create the chat API endpoint**

Create `web/api/chat.ts`:

```typescript
import { streamText, stepCountIs } from 'ai';
import { SYSTEM_PROMPT } from '../lib/agents/system-prompt';
import { lookupSchemaTool } from '../lib/tools/lookup-schema';
import { generateQueryTool } from '../lib/tools/generate-query';

export const config = { runtime: 'nodejs', maxDuration: 120 };

export default async function handler(req: Request): Promise<Response> {
  if (req.method === 'OPTIONS') {
    return new Response(null, {
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type',
      },
    });
  }

  if (req.method !== 'POST') {
    return new Response(JSON.stringify({ error: 'Method not allowed' }), {
      status: 405,
      headers: { 'Content-Type': 'application/json' },
    });
  }

  try {
    const { messages } = (await req.json()) as {
      messages: Array<{ role: 'user' | 'assistant'; content: string }>;
    };

    const result = streamText({
      model: 'anthropic/claude-opus-4.6',
      system: SYSTEM_PROMPT,
      messages,
      tools: {
        lookup_schema: lookupSchemaTool,
        generate_query: generateQueryTool,
      },
      stopWhen: stepCountIs(8),
      maxOutputTokens: 4096,
    });

    // Stream as NDJSON — each line is a JSON object from fullStream
    const encoder = new TextEncoder();
    const stream = new ReadableStream({
      async start(controller) {
        try {
          for await (const part of result.fullStream) {
            controller.enqueue(encoder.encode(JSON.stringify(part) + '\n'));
          }
        } catch (e) {
          controller.enqueue(encoder.encode(
            JSON.stringify({ type: 'error', error: e instanceof Error ? e.message : String(e) }) + '\n'
          ));
        } finally {
          controller.close();
        }
      },
    });

    return new Response(stream, {
      headers: {
        'Content-Type': 'application/x-ndjson',
        'Cache-Control': 'no-cache',
        'Access-Control-Allow-Origin': '*',
      },
    });
  } catch (e) {
    return new Response(
      JSON.stringify({ error: e instanceof Error ? e.message : String(e) }),
      { status: 500, headers: { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' } }
    );
  }
}
```

- [ ] **Step 3: Update vercel.json**

Replace `web/vercel.json` with:

```json
{
  "builds": [
    { "src": "api/chat.ts", "use": "@vercel/node" },
    { "src": "api/*.py", "use": "@vercel/python" },
    { "src": "public/**", "use": "@vercel/static" }
  ],
  "routes": [
    { "src": "/api/chat", "dest": "api/chat.ts" },
    { "src": "/api/query", "dest": "api/query.py" },
    { "src": "/api/export", "dest": "api/export.py" },
    { "src": "/api/lookups", "dest": "api/lookups.py" },
    { "src": "/(.*)", "dest": "public/$1" }
  ]
}
```

- [ ] **Step 4: Type-check**

```bash
cd /home/user/blumbergs-main/.worktrees/nl-query-agent/web && npx tsc --noEmit
```

Expected: No type errors.

- [ ] **Step 5: Commit**

```bash
cd /home/user/blumbergs-main/.worktrees/nl-query-agent
git add web/lib/agents/system-prompt.ts web/api/chat.ts web/vercel.json
git commit -m "feat: add chat API endpoint with system prompt and tool-loop agent"
```

---

### Task 5: Frontend Chat Sidebar — CSS

**Files:**
- Modify: `data-explorer.html` (insert CSS before `</style>`)

- [ ] **Step 1: Add sidebar CSS**

Insert the following CSS rules before the closing `</style>` tag (after the `.status` rule around line 125):

```css
/* -- AI Chat Sidebar -- */
.ai-toggle{position:fixed;left:0;top:50%;transform:translateY(-50%);z-index:100;
  background:var(--accent2);color:#fff;border:none;border-radius:0 6px 6px 0;
  padding:10px 6px;cursor:pointer;font-size:12px;font-weight:700;writing-mode:vertical-rl;
  letter-spacing:1px;opacity:.85;transition:opacity .2s}
.ai-toggle:hover{opacity:1}
.ai-toggle.hidden{display:none}
.ai-sidebar{width:0;min-width:0;overflow:hidden;transition:width .2s,min-width .2s;
  background:var(--surface);border-right:1px solid var(--border);display:flex;flex-direction:column}
.ai-sidebar.open{width:340px;min-width:340px}
.ai-header{display:flex;align-items:center;justify-content:space-between;padding:10px 12px;
  border-bottom:1px solid var(--border);background:var(--surface2)}
.ai-header h2{font-size:13px;color:var(--accent2);margin:0}
.ai-close{background:0;border:0;font-size:16px;cursor:pointer;color:var(--dim);padding:0 4px}
.ai-close:hover{color:var(--accent)}
.ai-messages{flex:1;overflow-y:auto;padding:10px;display:flex;flex-direction:column;gap:8px}
.ai-msg{max-width:95%;padding:8px 10px;border-radius:8px;font-size:12px;line-height:1.5;word-wrap:break-word}
.ai-msg.user{align-self:flex-end;background:var(--accent2);color:#fff;border-bottom-right-radius:2px}
.ai-msg.assistant{align-self:flex-start;background:var(--surface2);color:var(--text);border-bottom-left-radius:2px}
.ai-msg.error{align-self:center;background:#fef2f2;color:var(--accent);border:1px solid #fecaca;font-size:11px}
.ai-msg .sql-block{background:var(--bg);padding:6px 8px;border-radius:4px;font-family:'SF Mono','Cascadia Code',monospace;
  font-size:11px;margin-top:6px;white-space:pre-wrap;word-break:break-all;max-height:200px;overflow:auto}
.ai-msg .review-btn{display:inline-block;margin-top:6px;padding:4px 12px;background:var(--accent2);color:#fff;
  border:none;border-radius:4px;font-size:11px;font-weight:600;cursor:pointer}
.ai-msg .review-btn:hover{opacity:.85}
.ai-typing{align-self:flex-start;padding:8px 10px;font-size:11px;color:var(--dim);font-style:italic}
.ai-input-row{display:flex;gap:6px;padding:10px;border-top:1px solid var(--border);background:var(--surface)}
.ai-input-row input{flex:1;padding:7px 10px;font-size:12px;background:var(--bg);border:1px solid var(--border);
  border-radius:6px;color:var(--text);font-family:inherit}
.ai-input-row input:focus{outline:0;border-color:var(--accent2)}
.ai-input-row button{padding:7px 14px;background:var(--accent2);color:#fff;border:none;border-radius:6px;
  font-size:11px;font-weight:700;cursor:pointer}
.ai-input-row button:hover{opacity:.85}
.ai-input-row button:disabled{opacity:.4;cursor:not-allowed}
```

- [ ] **Step 2: Commit**

```bash
cd /home/user/blumbergs-main/.worktrees/nl-query-agent
git add data-explorer.html
git commit -m "style: add chat sidebar CSS to data-explorer"
```

---

### Task 6: Frontend Chat Sidebar — HTML

**Files:**
- Modify: `data-explorer.html` (add sidebar markup)

- [ ] **Step 1: Add sidebar HTML**

Replace `<div class="app">` (line 129) with:

```html
<button class="ai-toggle" id="ai-toggle">AI</button>
<div class="app">
<div class="ai-sidebar" id="ai-sidebar">
  <div class="ai-header">
    <h2>AI Query Assistant</h2>
    <button class="ai-close" id="ai-close">&times;</button>
  </div>
  <div class="ai-messages" id="ai-messages"></div>
  <div class="ai-input-row">
    <input type="text" id="ai-input" placeholder="Ask about charities data...">
    <button id="ai-send">Send</button>
  </div>
</div>
```

The existing `<div class="ctrl">` follows immediately after — no changes to it. The sidebar is the first child of `.app`.

- [ ] **Step 2: Commit**

```bash
cd /home/user/blumbergs-main/.worktrees/nl-query-agent
git add data-explorer.html
git commit -m "feat: add chat sidebar HTML to data-explorer"
```

---

### Task 7: Frontend Chat Sidebar — JavaScript

**Files:**
- Modify: `data-explorer.html` (add JS before `</script>`)

All DOM content is constructed using safe methods (`document.createElement`, `textContent`, `appendChild`). No use of `innerHTML` with untrusted content. The only use of `innerHTML` is for the existing `hl()` syntax highlighter which escapes all content via `escHtml()` before rendering.

- [ ] **Step 1: Add the sidebar JavaScript**

Insert the following JavaScript block before the closing `</script>` tag, after the existing `checkServer();` line. The code is wrapped in an IIFE.

The JS module does:

1. **Sidebar toggle**: Open/close sidebar, toggle visibility of the "AI" button.

2. **`addTextBubble(role, text)`**: Creates a message bubble using `document.createElement`. Sets `textContent` for user messages (plain text). For assistant messages, splits text on `\n` and creates separate `<span>` and `<br>` elements for line breaks. Returns the DOM element.

3. **`addQueryBubble(queryData, validationResult)`**: Builds a query display bubble with:
   - A bold "Generated Query" label (`<strong>`)
   - A `<pre class="sql-block">` with the SQL as `textContent`
   - An explanation paragraph as `textContent`
   - A "Review & Run" button if validation passed
   - Stores `queryData` on the button element via `button._queryData`

4. **`showTyping()` / `hideTyping()`**: Manages a "Thinking..." indicator element.

5. **`sendMessage()`**: Async function that:
   - Reads input value, clears input
   - Adds user bubble
   - Appends to `chatMessages` array
   - POSTs to `/api/chat` with `{messages: chatMessages}`
   - Reads the NDJSON response stream line by line
   - For `text-delta` parts: appends text to a running assistant bubble (creating text nodes)
   - For `tool-call` parts where `toolName === 'generate_query'`: captures `args` (sql, explanation, explorer_state)
   - For `tool-result` parts where `toolName === 'generate_query'`: calls `addQueryBubble` with captured args + result
   - For `error` parts: adds an error bubble
   - On stream end: saves assistant text to `chatMessages`

6. **`applyQueryToExplorer(queryData)`**: Called by the Review & Run button click handler:
   - Injects SQL into `document.getElementById('pre')` via the existing `hl()` function (which escapes content)
   - Opens the SQL panel if collapsed
   - Sets `S.prov`, `S.desig`, `S.cat` from `explorer_state.scope`
   - Sets `S.metrics` from `explorer_state.metrics` (filtered through `gm()` to validate IDs)
   - Updates metric chip `.on` classes
   - Sets `S.filters` from `explorer_state.filters`
   - Sets `S.sort`, `S.dir`, `S.lim`
   - Calls `sync()` then `update()` to refresh the explorer UI
   - Highlights the Run Query button with a temporary box-shadow

7. **Welcome message**: On load, calls `addTextBubble('assistant', ...)` with example questions.

8. **Event listeners**: `sendBtn.onclick = sendMessage`, Enter key in input sends message.

Key safety measures:
- All user-provided text rendered via `textContent` (never interpreted as HTML)
- SQL rendered via `textContent` on a `<pre>` element
- The only place HTML is generated is the existing `hl()` function for syntax highlighting, which uses `escHtml()` internally
- `_queryData` is stored on DOM elements as a JS object reference, never serialized to HTML

- [ ] **Step 2: Commit**

```bash
cd /home/user/blumbergs-main/.worktrees/nl-query-agent
git add data-explorer.html
git commit -m "feat: add chat sidebar JS with NDJSON stream parsing and explorer integration"
```

---

### Task 8: Sync and Final Polish

**Files:**
- Modify: `web/public/index.html` (sync from data-explorer.html)

- [ ] **Step 1: Sync to web/public/index.html**

```bash
cd /home/user/blumbergs-main/.worktrees/nl-query-agent
cp data-explorer.html web/public/index.html
```

- [ ] **Step 2: Type-check all TypeScript**

```bash
cd /home/user/blumbergs-main/.worktrees/nl-query-agent/web && npx tsc --noEmit
```

Expected: No errors.

- [ ] **Step 3: Verify all files present**

```bash
cd /home/user/blumbergs-main/.worktrees/nl-query-agent
echo "=== New files ===" && ls -la web/api/chat.ts web/lib/agents/system-prompt.ts web/lib/tools/lookup-schema.ts web/lib/tools/generate-query.ts web/lib/schema-index.json scripts/build_schema_index.py web/package.json web/tsconfig.json
```

Expected: All 8 files exist.

- [ ] **Step 4: Commit sync**

```bash
cd /home/user/blumbergs-main/.worktrees/nl-query-agent
git add web/public/index.html
git commit -m "chore: sync web/public/index.html with updated data-explorer.html"
```

---

### Task 9: Environment Setup and Verification

**Files:** None (configuration + manual testing)

- [ ] **Step 1: Set up environment variable**

On Vercel deployments, the AI Gateway authenticates automatically via OIDC — no key needed. For local development, pull the env config:

```bash
cd /home/user/blumbergs-main/.worktrees/nl-query-agent/web && vercel env pull .env.local
```

If OIDC is not configured, add an API key manually as a fallback:

```bash
cd /home/user/blumbergs-main/.worktrees/nl-query-agent/web && vercel env add AI_GATEWAY_API_KEY
```

Then pull it locally: `vercel env pull .env.local`

- [ ] **Step 2: Start dev server**

```bash
cd /home/user/blumbergs-main/.worktrees/nl-query-agent/web && vercel dev
```

Expected: Dev server starts on localhost:3000.

- [ ] **Step 3: Verify sidebar toggle**

Open `http://localhost:3000` in browser:
1. "AI" toggle button visible on left edge
2. Click it — sidebar opens (340px wide), explorer shifts right
3. Click X — sidebar closes
4. Welcome message visible with example questions

- [ ] **Step 4: Test a simple query**

Type: "Show me the 10 largest charities by total revenue"

Expected flow:
1. "Thinking..." appears
2. Agent text streams in (may call lookup_schema internally)
3. A "Generated Query" bubble appears with SQL and explanation
4. "Review & Run" button visible

- [ ] **Step 5: Test Review & Run integration**

Click "Review & Run":
1. SQL panel populates with highlighted SQL
2. Explorer scope/metrics update if explorer_state was provided
3. Run Query button gets highlighted glow
4. Click Run Query — results appear

- [ ] **Step 6: Test clarification flow**

Type: "Show me the biggest charities in Ontario"

Expected: Agent asks what "biggest" means (revenue, assets, expenditures?) as text. User responds. Agent then generates the query.

- [ ] **Step 7: Test out-of-scope question**

Type: "What's the weather?"

Expected: Agent responds that it can only help with Canadian charities data.
