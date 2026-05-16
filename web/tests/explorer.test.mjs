import { test } from 'node:test';
import assert from 'node:assert/strict';
import { M, PRESETS, genSQL, getMetric, needsTable, formatValue, columnTypeMap } from '../public/explorer.js';

// ── Helpers ────────────────────────────────────────────────────
function state(overrides = {}) {
  return {
    mode: 'detail', prov: '', desig: '', cat: '',
    gb: 'designation', aggfn: 'SUM',
    metrics: ['total_revenue'], filters: [],
    sort: 'total_revenue', dir: 'DESC', lim: 25,
    search: '', customWhere: '',
    ...overrides,
  };
}

// ── Catalog completeness ───────────────────────────────────────
test('every metric has id, label, group, table alias', () => {
  for (const m of M) {
    assert.ok(m.id, 'missing id');
    assert.ok(m.l,  `metric ${m.id} missing label`);
    assert.ok(m.g,  `metric ${m.id} missing group`);
    assert.ok(m.tb, `metric ${m.id} missing table alias`);
    // Either a column expression or a line number must be present
    assert.ok(m.col || m.ln, `metric ${m.id} missing col or ln`);
  }
});

test('labels reference CRA line numbers where applicable', () => {
  // Any metric that has a financial_d line number must say "line NNNN" in its label.
  const lined = M.filter(m => m.ln && m.tb === 'fd');
  for (const m of lined) {
    assert.match(m.l, /line \d{4}/, `metric ${m.id} (${m.l}) should mention CRA line number`);
  }
});

test('catalog includes the gifts metrics the user requested', () => {
  const ids = new Set(M.map(m => m.id));
  // Revenue side gifts
  for (const id of ['tax_receipted','ten_year_gifts_in','gifts_charities','non_receipted']) {
    assert.ok(ids.has(id), `missing gifts-in metric: ${id}`);
  }
  // Outgoing gifts
  for (const id of ['gifts_to_qds','grants_non_qds']) {
    assert.ok(ids.has(id), `missing gifts-out metric: ${id}`);
  }
  // Schedule 6 detail (gift table)
  for (const id of ['gift_total_amount','gift_in_kind','gift_donee_count']) {
    assert.ok(ids.has(id), `missing Sch 6 gift metric: ${id}`);
  }
  // Schedule 5 non-cash
  assert.ok(ids.has('noncash_total'), 'missing schedule 5 non-cash total');
});

test('catalog includes trustees metrics', () => {
  const ids = new Set(M.map(m => m.id));
  for (const id of ['num_trustees','num_arm_trustees','num_non_arm_trustees']) {
    assert.ok(ids.has(id), `missing trustees metric: ${id}`);
  }
});

test('catalog includes programs metrics with breakdown', () => {
  const ids = new Set(M.map(m => m.id));
  for (const id of ['num_programs','num_ongoing_programs','num_new_programs','num_inactive_programs']) {
    assert.ok(ids.has(id), `missing programs metric: ${id}`);
  }
});

test('preset "All Gifts" exists and references gift metrics', () => {
  const p = PRESETS.find(p => p.n === 'All Gifts');
  assert.ok(p, 'missing "All Gifts" preset');
  for (const id of ['tax_receipted','gifts_charities','non_receipted','gifts_to_qds']) {
    assert.ok(p.s.metrics.includes(id), `"All Gifts" preset missing ${id}`);
  }
});

test('preset "Trustees & Programs" exists', () => {
  const p = PRESETS.find(p => p.n === 'Trustees & Programs');
  assert.ok(p, 'missing "Trustees & Programs" preset');
  assert.ok(p.s.metrics.includes('num_trustees'), 'preset must include num_trustees');
  assert.ok(p.s.metrics.includes('num_programs'), 'preset must include num_programs');
});

// ── SQL generation: joins are conditional ───────────────────────
test('detail SQL with only fd metric: no extra CTEs or joins', () => {
  const sql = genSQL(state({ metrics: ['total_revenue'] }));
  assert.doesNotMatch(sql, /\bWITH\b/);
  assert.match(sql, /LEFT JOIN financial_d fd/);
  assert.doesNotMatch(sql, /gift_agg|trustee_agg|program_agg/);
});

test('selecting a trustees metric adds trustee_agg CTE and JOIN', () => {
  const sql = genSQL(state({ metrics: ['num_trustees'] }));
  assert.match(sql, /WITH\s+trustee_agg AS/);
  assert.match(sql, /LEFT JOIN trustee_agg tagg ON tagg\.bn = cb\.bn/);
  assert.match(sql, /SELECT.*tagg\.num_trustees AS num_trustees/s);
  // No need to join financial_d when only trustee metric is selected
  assert.doesNotMatch(sql, /LEFT JOIN financial_d/);
});

test('selecting a gift Schedule-6 metric adds gift_agg CTE and JOIN', () => {
  const sql = genSQL(state({
    metrics: ['gift_total_amount','gift_in_kind'],
    sort: 'gift_total_amount',
  }));
  assert.match(sql, /WITH\s+gift_agg AS/);
  assert.match(sql, /LEFT JOIN gift_agg gagg ON gagg\.bn = cb\.bn/);
  assert.match(sql, /gagg\.total_gifts AS gift_total_amount/);
  assert.match(sql, /gagg\.total_gifts_in_kind AS gift_in_kind/);
});

test('selecting program metrics adds program_agg CTE', () => {
  const sql = genSQL(state({ metrics: ['num_ongoing_programs','num_new_programs'] }));
  assert.match(sql, /WITH\s+program_agg AS/);
  assert.match(sql, /LEFT JOIN program_agg pagg ON pagg\.bn = cb\.bn/);
});

test('schedule 5 non-cash metric joins schedule_5_noncash with s5 alias', () => {
  const sql = genSQL(state({ metrics: ['noncash_total'] }));
  assert.match(sql, /LEFT JOIN schedule_5_noncash s5 ON s5\."BN\/Registration number" = cb\.bn/);
  assert.match(sql, /s5\."580"/);
});

test('multiple new tables combine cleanly with multiple CTEs', () => {
  const sql = genSQL(state({
    metrics: ['num_trustees','num_programs','gift_total_amount'],
    sort: 'num_trustees',
  }));
  // All three CTEs present
  assert.match(sql, /trustee_agg AS/);
  assert.match(sql, /program_agg AS/);
  assert.match(sql, /gift_agg AS/);
  // Joined as a single WITH … , … chain
  const withMatch = sql.match(/^WITH\s+([\s\S]+?)\nSELECT/);
  assert.ok(withMatch, 'expected a WITH … SELECT block');
});

test('aggregate mode + new metrics still works', () => {
  const sql = genSQL(state({
    mode: 'aggregate', gb: 'province',
    metrics: ['num_trustees','total_revenue'],
    sort: 'num_trustees',
  }));
  assert.match(sql, /SUM\(tagg\.num_trustees\) AS num_trustees/);
  assert.match(sql, /GROUP BY cb\.province/);
});

test('SQL must remain a valid SELECT (security boundary)', () => {
  const sql = genSQL(state({ metrics: ['total_revenue','num_trustees','gift_total_amount'] }));
  assert.match(sql.trimStart(), /^WITH|^SELECT/i);
  // No mutation keywords leak through
  assert.doesNotMatch(sql, /\bINSERT|UPDATE|DELETE|DROP|ALTER|TRUNCATE|ATTACH\b/i);
});

// ── Number formatting ──────────────────────────────────────────
test('formatValue: $ prefix and thousand separators for currency', () => {
  assert.equal(formatValue(1234567, '$'), '$1,234,567');
  assert.equal(formatValue(0, '$'), '$0');
  assert.equal(formatValue(-50000, '$'), '-$50,000');
});

test('formatValue: integers get separators, no decimals', () => {
  assert.equal(formatValue(12345, 'i'), '12,345');
  assert.equal(formatValue(0, 'i'), '0');
});

test('formatValue: null/empty renders as em dash', () => {
  assert.equal(formatValue(null, '$'), '—');
  assert.equal(formatValue(undefined, 'i'), '—');
  assert.equal(formatValue('', '$'), '—');
});

test('columnTypeMap maps metric ids to their currency/int markers', () => {
  const map = columnTypeMap(['total_revenue','num_trustees']);
  assert.equal(map.total_revenue, '$');
  assert.equal(map.num_trustees, 'i');
});

// ── needsTable helper ──────────────────────────────────────────
test('needsTable is false when nothing references that alias', () => {
  assert.equal(needsTable(state({ metrics: ['total_revenue'] }), 'tagg'), false);
});
test('needsTable picks up metrics referenced by filters too', () => {
  const s = state({
    metrics: ['total_revenue'],
    filters: [{ f: 'num_trustees', op: '>', v: '5' }],
  });
  assert.equal(needsTable(s, 'tagg'), true);
});
