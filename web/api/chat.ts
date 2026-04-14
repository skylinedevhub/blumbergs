import type { IncomingMessage, ServerResponse } from 'node:http';
import { streamText, stepCountIs, type ModelMessage, type LanguageModel } from 'ai';
import { gateway } from '@ai-sdk/gateway';
import { createAnthropic } from '@ai-sdk/anthropic';
import { createGoogleGenerativeAI } from '@ai-sdk/google';
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

function setCors(res: ServerResponse): void {
  for (const [k, v] of Object.entries(CORS_HEADERS)) {
    res.setHeader(k, v);
  }
}

/** True if the error is a rate-limit / overload that a different model might avoid. */
function isOverloadError(err: unknown): boolean {
  const msg = (err instanceof Error ? err.message : String(err)).toLowerCase();
  return (
    msg.includes('high demand') ||
    msg.includes('rate limit') ||
    msg.includes('rate_limit') ||
    msg.includes('overloaded') ||
    msg.includes('too many requests') ||
    msg.includes('429') ||
    msg.includes('529') ||
    msg.includes('503') ||
    msg.includes('capacity') ||
    msg.includes('retry')
  );
}

/**
 * Build an ordered list of models to try.
 * Primary = user's explicit choice; fallbacks = alternate providers.
 */
function buildModelChain(provider: string, apiKey?: string): LanguageModel[] {
  const models: LanguageModel[] = [];
  const serverGeminiKey = process.env.GOOGLE_GENERATIVE_AI_API_KEY;

  if (provider === 'anthropic' && apiKey) {
    // User provided their own Anthropic key
    models.push(createAnthropic({ apiKey })('claude-opus-4.6'));
    if (serverGeminiKey) {
      models.push(createGoogleGenerativeAI({ apiKey: serverGeminiKey })('gemini-2.5-pro'));
    }
    models.push(gateway('anthropic/claude-sonnet-4.6'));
  } else if (provider === 'google' && apiKey) {
    // User provided their own Google key
    models.push(createGoogleGenerativeAI({ apiKey })('gemini-2.5-pro'));
    models.push(gateway('anthropic/claude-sonnet-4.6'));
  } else {
    // Default: server Gemini → AI Gateway Anthropic
    if (serverGeminiKey) {
      models.push(createGoogleGenerativeAI({ apiKey: serverGeminiKey })('gemini-2.5-pro'));
    }
    models.push(gateway('anthropic/claude-sonnet-4.6'));
  }

  return models;
}

export default async function handler(
  req: IncomingMessage,
  res: ServerResponse
): Promise<void> {
  // Handle CORS preflight
  if (req.method === 'OPTIONS') {
    setCors(res);
    res.writeHead(204);
    res.end();
    return;
  }

  if (req.method !== 'POST') {
    setCors(res);
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
  } catch {
    setCors(res);
    res.writeHead(400, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ error: 'Failed to read request body' }));
    return;
  }

  let messages: ModelMessage[];
  let provider: string;
  let apiKey: string | undefined;
  try {
    const parsed = JSON.parse(body) as { messages: unknown; provider?: string; apiKey?: string };
    if (!Array.isArray(parsed.messages)) {
      throw new Error('messages must be an array');
    }
    messages = parsed.messages as ModelMessage[];
    provider = parsed.provider || 'gateway';
    apiKey = parsed.apiKey;
  } catch {
    setCors(res);
    res.writeHead(400, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ error: 'Invalid JSON body — expected { messages: [...] }' }));
    return;
  }

  // Build model fallback chain
  const models = buildModelChain(provider, apiKey);

  // ── Try each model until one produces a working stream ──
  // We await the FIRST event before sending 200 headers. This lets us
  // catch overload errors and fall back to the next model transparently,
  // or return a proper 503 if all models are busy.

  let workingIter: AsyncIterator<any> | null = null;
  let firstEvent: IteratorResult<any> | null = null;
  let lastError: Error | null = null;

  const streamConfig = {
    system: SYSTEM_PROMPT,
    messages,
    tools: {
      lookup_schema: lookupSchema,
      generate_query: generateQuery,
    },
    stopWhen: stepCountIs(8),
    maxOutputTokens: 4096,
  };

  for (const model of models) {
    try {
      const result = streamText({ ...streamConfig, model });
      const iter = result.fullStream[Symbol.asyncIterator]();
      // Await first event — this is where overload errors surface
      const first = await iter.next();
      // If we reach here, the model is responding
      workingIter = iter;
      firstEvent = first;
      lastError = null;
      break;
    } catch (err) {
      lastError = err as Error;
      if (isOverloadError(err)) {
        continue; // try next model
      }
      break; // non-retryable error, stop trying
    }
  }

  // All models failed — return a proper HTTP error
  if (!workingIter || !firstEvent) {
    setCors(res);
    const friendly = isOverloadError(lastError)
      ? 'All AI models are currently busy. Please try again in a moment.'
      : `AI error: ${lastError?.message || 'Unknown error'}`;
    const status = isOverloadError(lastError) ? 503 : 500;
    res.writeHead(status, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({
      error: friendly,
      retryable: isOverloadError(lastError),
    }));
    return;
  }

  // ── Model is working — commit to streaming ──
  setCors(res);
  res.setHeader('Content-Type', 'application/x-ndjson');
  res.setHeader('Transfer-Encoding', 'chunked');
  res.writeHead(200);

  /** Serialize a fullStream part to an NDJSON event line (or null to skip). */
  function toNdjson(part: any): string | null {
    switch (part.type) {
      case 'text-delta':
        return JSON.stringify({
          type: 'text-delta',
          textDelta: String(part.textDelta ?? part.text ?? ''),
        });
      case 'tool-call':
        return JSON.stringify({
          type: 'tool-call',
          toolName: part.toolName,
          toolCallId: part.toolCallId,
          args: part.input ?? part.args,
        });
      case 'tool-result':
        return JSON.stringify({
          type: 'tool-result',
          toolName: part.toolName,
          toolCallId: part.toolCallId,
          result: part.output ?? part.result,
        });
      case 'error':
        return JSON.stringify({ type: 'error', error: String(part.error) });
      case 'finish':
        return JSON.stringify({ type: 'finish' });
      default:
        return null; // step-finish, tool-call-streaming-start, etc.
    }
  }

  try {
    // Write the buffered first event
    if (!firstEvent.done) {
      const line = toNdjson(firstEvent.value);
      if (line) res.write(line + '\n');
    }

    // Continue streaming remaining events
    while (true) {
      const next = await workingIter.next();
      if (next.done) break;
      const line = toNdjson(next.value);
      if (line) res.write(line + '\n');
    }
  } catch (err) {
    // Mid-stream error (rare) — send as NDJSON error event
    const message = err instanceof Error ? err.message : String(err);
    res.write(JSON.stringify({ type: 'error', error: message }) + '\n');
  } finally {
    res.end();
  }
}
