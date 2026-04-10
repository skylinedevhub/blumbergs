import type { IncomingMessage, ServerResponse } from 'node:http';
import { streamText, stepCountIs, type ModelMessage } from 'ai';
import { gateway } from '@ai-sdk/gateway';
import { SYSTEM_PROMPT } from '../lib/agents/system-prompt.js';
import { lookupSchema } from '../lib/tools/lookup-schema.js';
import { generateQuery } from '../lib/tools/generate-query.js';

export const config = {
  runtime: 'nodejs',
  maxDuration: 120,
};

const CORS_HEADERS = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'POST, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type',
};

export default async function handler(
  req: IncomingMessage,
  res: ServerResponse
): Promise<void> {
  // Handle CORS preflight
  if (req.method === 'OPTIONS') {
    for (const [k, v] of Object.entries(CORS_HEADERS)) {
      res.setHeader(k, v);
    }
    res.writeHead(204);
    res.end();
    return;
  }

  if (req.method !== 'POST') {
    for (const [k, v] of Object.entries(CORS_HEADERS)) {
      res.setHeader(k, v);
    }
    res.writeHead(405, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ error: 'Method not allowed' }));
    return;
  }

  // Parse request body
  let body: string;
  try {
    body = await new Promise<string>((resolve, reject) => {
      const chunks: Buffer[] = [];
      req.on('data', (chunk: Buffer) => chunks.push(chunk));
      req.on('end', () => resolve(Buffer.concat(chunks).toString()));
      req.on('error', reject);
    });
  } catch (err) {
    for (const [k, v] of Object.entries(CORS_HEADERS)) {
      res.setHeader(k, v);
    }
    res.writeHead(400, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ error: 'Failed to read request body' }));
    return;
  }

  let messages: ModelMessage[];
  try {
    const parsed = JSON.parse(body) as { messages: unknown };
    if (!Array.isArray(parsed.messages)) {
      throw new Error('messages must be an array');
    }
    messages = parsed.messages as ModelMessage[];
  } catch (err) {
    for (const [k, v] of Object.entries(CORS_HEADERS)) {
      res.setHeader(k, v);
    }
    res.writeHead(400, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ error: 'Invalid JSON body — expected { messages: [...] }' }));
    return;
  }

  // Set response headers for NDJSON streaming
  for (const [k, v] of Object.entries(CORS_HEADERS)) {
    res.setHeader(k, v);
  }
  res.setHeader('Content-Type', 'application/x-ndjson');
  res.setHeader('Transfer-Encoding', 'chunked');
  res.writeHead(200);

  try {
    const result = streamText({
      model: gateway('anthropic/claude-opus-4.6'),
      system: SYSTEM_PROMPT,
      messages,
      tools: {
        lookup_schema: lookupSchema,
        generate_query: generateQuery,
      },
      stopWhen: stepCountIs(8),
      maxOutputTokens: 4096,
    });

    for await (const part of result.fullStream) {
      const line = JSON.stringify(part);
      res.write(line + '\n');
    }
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    const errorLine = JSON.stringify({ type: 'error', error: message });
    res.write(errorLine + '\n');
  } finally {
    res.end();
  }
}
