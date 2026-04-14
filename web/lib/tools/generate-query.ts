import { tool } from 'ai';
import { z } from 'zod';

const baseUrl =
  process.env.VERCEL_URL
    ? `https://${process.env.VERCEL_URL}`
    : 'http://localhost:3000';

export const generateQuery = tool({
  description:
    'Submit a generated SQL SELECT query for validation. The query is validated by running it with LIMIT 0 against the live database. ' +
    'On success, returns column names. On error, returns the error message with a hint to fix and retry. ' +
    'Always call this after composing SQL — never present unvalidated SQL to the user.',
  inputSchema: z.object({
    sql: z.string().describe('The SELECT query to validate (do not include LIMIT yourself — it is appended automatically)'),
    explanation: z
      .string()
      .describe('Plain English description of what this query does and what the results represent'),
    explorer_state: z
      .object({
        scope: z.object({
          province: z.string().optional().describe('Province code: ON, QC, BC, AB, MB, SK, NS, NB, NL, PE, NT, NU, YT'),
          designation: z.string().optional().describe('Designation code: A (Public Foundation), B (Private Foundation), C (Charitable Org)'),
          category: z.string().optional().describe('Category code from lookup_category'),
        }).optional(),
        metrics: z
          .array(z.string())
          .optional()
          .describe('Metric IDs in {alias}_{line} format, e.g. ["fd_4700", "fd_5100"]'),
        filters: z
          .array(z.object({
            column: z.string().describe('Metric ID, e.g. "fd_4700"'),
            operator: z.string().describe('SQL operator: >, >=, <, <=, =, !=, ILIKE'),
            value: z.string().describe('Filter value'),
          }))
          .optional(),
        sort: z.object({
          column: z.string().describe('Metric ID to sort by, e.g. "fd_4700"'),
          direction: z.enum(['ASC', 'DESC']).describe('Sort direction'),
        }).optional(),
        limit: z.number().optional().describe('Row limit, e.g. 25'),
      })
      .optional()
      .describe('Maps query to the Data Explorer UI controls'),
  }),
  execute: async ({ sql }) => {
    const validationSql = sql.trimEnd().replace(/;?\s*$/, '') + ' LIMIT 0';

    try {
      const response = await fetch(`${baseUrl}/api/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sql: validationSql }),
      });

      if (!response.ok && response.status === 401) {
        // Auth-protected deployment — skip validation
        return {
          valid: true as const,
          columns: [] as string[],
          warning: 'Could not validate (deployment is auth-protected). SQL has not been checked.',
        };
      }

      const data = (await response.json()) as
        | { columns: string[]; rows: unknown[]; count: number; time: number }
        | { error: string };

      if ('error' in data) {
        return {
          valid: false as const,
          error: data.error,
          hint: 'Fix the SQL error and retry with generate_query.',
        };
      }

      return {
        valid: true as const,
        columns: data.columns,
      };
    } catch {
      // Validation endpoint unreachable (e.g., Vercel auth on preview deploys).
      // Return as unvalidated — the user will review the SQL before running it.
      return {
        valid: true as const,
        columns: [] as string[],
        warning: 'Could not validate query (validation endpoint unreachable). The SQL has not been checked for errors.',
      };
    }
  },
});
