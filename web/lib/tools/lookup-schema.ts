import { tool } from 'ai';
import { z } from 'zod';
import schemaIndex from '../schema-index.json' with { type: 'json' };

type SchemaIndex = typeof schemaIndex;
type Tables = SchemaIndex['tables'];
type Views = SchemaIndex['views'];
type DomainValues = SchemaIndex['domain_values'];
type Quirks = SchemaIndex['quirks'];

function matchesQuery(text: string | undefined | null, query: string): boolean {
  if (!text) return false;
  return text.toLowerCase().includes(query.toLowerCase());
}

function searchTable(
  name: string,
  table: Tables[keyof Tables],
  query: string
): boolean {
  if (matchesQuery(name, query)) return true;
  if ('description' in table && matchesQuery(table.description as string, query)) return true;
  const columns = (table as { columns?: Record<string, { type: string; description?: string; line?: string }> }).columns;
  if (columns) {
    for (const [colName, colDef] of Object.entries(columns)) {
      if (matchesQuery(colName, query)) return true;
      if (colDef.description && matchesQuery(colDef.description, query)) return true;
      if (colDef.line && matchesQuery(colDef.line, query)) return true;
    }
  }
  return false;
}

function searchView(
  name: string,
  view: Views[keyof Views],
  query: string
): boolean {
  if (matchesQuery(name, query)) return true;
  if ('description' in view && matchesQuery(view.description as string, query)) return true;
  const columns = (view as { columns?: Record<string, { type: string; description?: string }> }).columns;
  if (columns) {
    for (const [colName, colDef] of Object.entries(columns)) {
      if (matchesQuery(colName, query)) return true;
      if (colDef.description && matchesQuery(colDef.description, query)) return true;
    }
  }
  return false;
}

export const lookupSchema = tool({
  description:
    'Search the database schema index for tables, columns, views, and domain values by keyword. ' +
    'Use this before generating SQL to confirm table names, column names, T3010 line numbers, and join patterns.',
  inputSchema: z.object({
    query: z
      .string()
      .describe(
        'Search term — table name, column name, T3010 line number, or domain concept (e.g. "revenue", "4700", "designation", "compensation")'
      ),
  }),
  execute: async ({ query }) => {
    // Search tables
    const matchedTables: Record<string, unknown> = {};
    for (const [name, table] of Object.entries(schemaIndex.tables as Tables)) {
      if (searchTable(name, table, query)) {
        matchedTables[name] = table;
      }
    }

    // Search views
    const matchedViews: Record<string, unknown> = {};
    for (const [name, view] of Object.entries(schemaIndex.views as Views)) {
      if (searchView(name, view, query)) {
        matchedViews[name] = view;
      }
    }

    // Search domain_values
    const matchedDomainValues: Record<string, unknown> = {};
    for (const [key, values] of Object.entries(schemaIndex.domain_values as DomainValues)) {
      if (matchesQuery(key, query)) {
        matchedDomainValues[key] = values;
      } else if (typeof values === 'object' && values !== null) {
        // Check if any value in the domain values matches
        const hasMatch = Object.entries(values as Record<string, string>).some(
          ([k, v]) => matchesQuery(k, query) || matchesQuery(v, query)
        );
        if (hasMatch) {
          matchedDomainValues[key] = values;
        }
      }
    }

    // Search quirks
    const matchedQuirks = (schemaIndex.quirks as Quirks).filter(
      (q) => matchesQuery(typeof q === 'string' ? q : JSON.stringify(q), query)
    );

    return {
      tables: matchedTables,
      views: matchedViews,
      domainValues: matchedDomainValues,
      quirks: matchedQuirks,
    };
  },
});
