/* eslint-disable */
// T3010 Data Explorer — pure functions module.
// Dual-load: ESM `import` from Node tests; browser <script> assigns to
// globalThis.Explorer for the legacy inline script in index.html.

// ── CRA T3010 metric catalog ───────────────────────────────────
// Label conventions:
//   - Exact CRA wording from the T3010 form
//   - Line number appended as "(line NNNN)" so users know which line is being queried
//   - tb (table alias): fd=financial_d, sc=schedule_3_compensation, cc=charity_counts,
//                       s5=schedule_5_noncash, gagg=gift_agg, tagg=trustee_agg, pagg=program_agg
//   - t: '$' currency (TEXT in DB, needs money()), 'i' integer, 'n' numeric already
const M = [
  // ── Revenue (Section D) ──
  {id:'total_revenue',      l:'Total revenue (line 4700)',                                    ln:'4700',t:'$',g:'Revenue',                tb:'fd'},
  {id:'tax_receipted',      l:'Tax-receipted gifts (line 4500)',                              ln:'4500',t:'$',g:'Revenue — Gifts In',     tb:'fd'},
  {id:'ten_year_gifts_in',  l:'10-year gifts received (line 4505)',                           ln:'4505',t:'$',g:'Revenue — Gifts In',     tb:'fd'},
  {id:'gifts_charities',    l:'Gifts from other registered charities (line 4510)',           ln:'4510',t:'$',g:'Revenue — Gifts In',     tb:'fd'},
  {id:'non_receipted',      l:'Other gifts not tax-receipted (line 4530)',                    ln:'4530',t:'$',g:'Revenue — Gifts In',     tb:'fd'},
  {id:'govt_federal',       l:'Federal government funding (line 4540)',                       ln:'4540',t:'$',g:'Revenue',                tb:'fd'},
  {id:'govt_provincial',    l:'Provincial/territorial government funding (line 4550)',        ln:'4550',t:'$',g:'Revenue',                tb:'fd'},
  {id:'govt_municipal',     l:'Municipal/regional government funding (line 4560)',            ln:'4560',t:'$',g:'Revenue',                tb:'fd'},
  {id:'receipted_outside',  l:'Tax-receipted from outside Canada (line 4575, V24)',           ln:'4575',t:'$',g:'Revenue',                tb:'fd'},
  {id:'investment_income',  l:'Interest and investment income (line 4580, V24)',              ln:'4580',t:'$',g:'Revenue',                tb:'fd'},
  {id:'fundraising_rev',    l:'Revenue from fundraising (line 4630)',                         ln:'4630',t:'$',g:'Revenue',                tb:'fd'},
  {id:'sale_goods',         l:'Revenue from sale of goods/services (line 4640)',              ln:'4640',t:'$',g:'Revenue',                tb:'fd'},
  {id:'other_revenue',      l:'Revenue from all other sources (line 4650)',                   ln:'4650',t:'$',g:'Revenue',                tb:'fd'},

  // ── Expenditures (Section D) ──
  {id:'total_expenditures', l:'Total expenditures (line 5100)',                               ln:'5100',t:'$',g:'Expenditures',           tb:'fd'},
  {id:'charitable_programs',l:'Charitable activities (line 5000)',                            ln:'5000',t:'$',g:'Expenditures',           tb:'fd'},
  {id:'mgmt_admin',         l:'Management and administration (line 5010)',                    ln:'5010',t:'$',g:'Expenditures',           tb:'fd'},
  {id:'fundraising_exp',    l:'Fundraising (line 5020)',                                      ln:'5020',t:'$',g:'Expenditures',           tb:'fd'},
  {id:'political',          l:'Political activities (line 5030)',                             ln:'5030',t:'$',g:'Expenditures',           tb:'fd'},
  {id:'gifts_to_qds',       l:'Gifts to qualified donees (line 5050)',                        ln:'5050',t:'$',g:'Expenditures — Gifts Out',tb:'fd'},
  {id:'grants_non_qds',     l:'Grants to non-qualified donees (line 5045)',                   ln:'5045',t:'$',g:'Expenditures — Gifts Out',tb:'fd'},

  // ── Balance Sheet ──
  {id:'total_assets',       l:'Total assets (line 4200)',                                     ln:'4200',t:'$',g:'Balance Sheet',          tb:'fd'},
  {id:'total_liabilities',  l:'Total liabilities (line 4350)',                                ln:'4350',t:'$',g:'Balance Sheet',          tb:'fd'},
  {id:'cash_investments',   l:'Cash, bank accounts, and short-term investments (line 4100)', ln:'4100',t:'$',g:'Balance Sheet',          tb:'fd'},
  {id:'long_term_invest',   l:'Long-term investments (line 4140)',                            ln:'4140',t:'$',g:'Balance Sheet',          tb:'fd'},
  {id:'assets_non_charit',  l:'Assets not used in charitable activities (line 4250)',         ln:'4250',t:'$',g:'Balance Sheet',          tb:'fd'},

  // ── Employment (Schedule 3) ──
  {id:'ft_employees',       l:'Permanent full-time positions (Sch 3 line 300)',               col:'"300"',t:'i',g:'Employment',         tb:'sc'},
  {id:'pt_employees',       l:'Part-time / part-year positions (Sch 3 line 370)',             col:'"370"',t:'i',g:'Employment',         tb:'sc'},
  {id:'total_compensation', l:'Total expenditure on compensation (Sch 3 line 390)',           col:'"390"',t:'$',g:'Employment',         tb:'sc'},
  {id:'compensation_fd',    l:'Total compensation reported in Section D (line 4880)',         ln:'4880',  t:'$',g:'Employment',         tb:'fd'},

  // ── Schedule 6: Detailed gifts to qualified donees (T1236) ──
  {id:'gift_total_amount',  l:'Total gifts to qualified donees (Sch 6 sum)',                  col:'total_gifts',          t:'$',g:'Schedule 6 — Gifts Detail', tb:'gagg'},
  {id:'gift_in_kind',       l:'Gifts in kind to qualified donees (Sch 6 sum)',                col:'total_gifts_in_kind',  t:'$',g:'Schedule 6 — Gifts Detail', tb:'gagg'},
  {id:'gift_donee_count',   l:'Number of qualified donees gifted to (Sch 6)',                 col:'num_donees',           t:'i',g:'Schedule 6 — Gifts Detail', tb:'gagg'},
  {id:'gift_political',     l:'Gifts for political activities (Sch 6 sum)',                   col:'total_political_gifts',t:'$',g:'Schedule 6 — Gifts Detail', tb:'gagg'},

  // ── Schedule 5: Non-cash gifts received ──
  {id:'noncash_total',      l:'Total non-cash gifts received (Sch 5 line 580)',               ln:'580',t:'$',g:'Schedule 5 — Non-Cash Gifts', tb:'s5'},
  {id:'noncash_securities', l:'Non-cash gifts: publicly traded securities (Sch 5 line 500)',  ln:'500',t:'$',g:'Schedule 5 — Non-Cash Gifts', tb:'s5'},
  {id:'noncash_real_prop',  l:'Non-cash gifts: real property (Sch 5 line 540)',               ln:'540',t:'$',g:'Schedule 5 — Non-Cash Gifts', tb:'s5'},

  // ── Trustees / Directors (Section B) ──
  {id:'num_trustees',         l:'Number of directors/trustees',                               col:'num_trustees',         t:'i',g:'Directors & Trustees', tb:'tagg'},
  {id:'num_arm_trustees',     l:'Directors/trustees at arm’s length',                    col:'num_arm_trustees',     t:'i',g:'Directors & Trustees', tb:'tagg'},
  {id:'num_non_arm_trustees', l:'Directors/trustees not at arm’s length',                col:'num_non_arm_trustees', t:'i',g:'Directors & Trustees', tb:'tagg'},

  // ── Programs (Section C) ──
  {id:'num_programs',         l:'Number of programs reported',                                col:'num_programs',          t:'i',g:'Programs (Section C)', tb:'pagg'},
  {id:'num_ongoing_programs', l:'Ongoing programs (OP)',                                      col:'num_ongoing_programs',  t:'i',g:'Programs (Section C)', tb:'pagg'},
  {id:'num_new_programs',     l:'New programs (NP)',                                          col:'num_new_programs',      t:'i',g:'Programs (Section C)', tb:'pagg'},
  {id:'num_inactive_programs',l:'Inactive programs (NA)',                                     col:'num_inactive_programs', t:'i',g:'Programs (Section C)', tb:'pagg'},

  // ── Foreign activity (charity_counts) ──
  {id:'num_grants',         l:'Number of grants to non-qualified donees',     col:'num_grants',             t:'i',g:'Foreign Activity',tb:'cc'},
  {id:'num_countries',      l:'Number of countries of operation',             col:'num_operating_countries',t:'i',g:'Foreign Activity',tb:'cc'},
];

const PRESETS = [
  {n:'Sector Overview', s:{mode:'aggregate',prov:'',desig:'',cat:'',gb:'designation',aggfn:'SUM',
    metrics:['total_revenue','total_expenditures','total_assets','total_compensation'],
    filters:[],sort:'total_revenue',dir:'DESC',lim:25,search:'',customWhere:''}},
  {n:'By Province', s:{mode:'aggregate',prov:'',desig:'',cat:'',gb:'province',aggfn:'SUM',
    metrics:['total_revenue','total_expenditures','ft_employees'],
    filters:[],sort:'total_revenue',dir:'DESC',lim:25,search:'',customWhere:''}},
  {n:'Top 25 Revenue', s:{mode:'detail',prov:'',desig:'',cat:'',gb:'designation',aggfn:'SUM',
    metrics:['total_revenue','total_expenditures','total_assets'],
    filters:[],sort:'total_revenue',dir:'DESC',lim:25,search:'',customWhere:''}},
  {n:'Top Employers', s:{mode:'detail',prov:'',desig:'',cat:'',gb:'designation',aggfn:'SUM',
    metrics:['ft_employees','pt_employees','total_compensation'],
    filters:[],sort:'ft_employees',dir:'DESC',lim:25,search:'',customWhere:''}},
  {n:'Foreign Activity', s:{mode:'detail',prov:'',desig:'',cat:'',gb:'designation',aggfn:'SUM',
    metrics:['total_revenue','num_countries','num_grants'],
    filters:[{f:'num_countries',op:'>',v:'0'}],sort:'num_countries',dir:'DESC',lim:50,search:'',customWhere:''}},
  {n:'Foundations Only', s:{mode:'detail',prov:'',desig:'A',cat:'',gb:'designation',aggfn:'SUM',
    metrics:['total_revenue','total_assets','gifts_to_qds'],
    filters:[],sort:'total_assets',dir:'DESC',lim:25,search:'',customWhere:''}},
  {n:'All Gifts', s:{mode:'detail',prov:'',desig:'',cat:'',gb:'designation',aggfn:'SUM',
    metrics:['tax_receipted','gifts_charities','non_receipted','ten_year_gifts_in','gifts_to_qds','grants_non_qds','noncash_total'],
    filters:[],sort:'tax_receipted',dir:'DESC',lim:25,search:'',customWhere:''}},
  {n:'Trustees & Programs', s:{mode:'detail',prov:'',desig:'',cat:'',gb:'designation',aggfn:'SUM',
    metrics:['num_trustees','num_arm_trustees','num_non_arm_trustees','num_programs','num_ongoing_programs'],
    filters:[],sort:'num_trustees',dir:'DESC',lim:25,search:'',customWhere:''}},
];

// ── Helpers ─────────────────────────────────────────────────────
const getMetric = function(id, catalog){ catalog = catalog || M; return catalog.find(function(m){return m.id===id}); };

const needsTable = function(state, alias, catalog){
  catalog = catalog || M;
  return state.metrics.some(function(id){var m=getMetric(id,catalog);return m&&m.tb===alias;}) ||
         state.filters.some(function(f){var m=getMetric(f.f,catalog);return m&&m.tb===alias;});
};

function colRef(m){
  if(m.ln && m.tb==='fd') return 'fd."'+m.ln+'"';
  if(m.ln && m.tb==='s5') return 's5."'+m.ln+'"';
  return m.tb+'.'+m.col;
}

// CTE-derived tables (gift_agg, trustee_agg, program_agg) already produce
// numeric columns inside the CTE — no outer money() wrapper needed.
const CTE_TABLES = ['gagg','tagg','pagg'];
function isAlreadyNumeric(m){
  return m.t === 'i' || m.t === 'n' || CTE_TABLES.indexOf(m.tb) >= 0;
}

function moneyExpr(m){
  if(isAlreadyNumeric(m)) return colRef(m);
  return 'money('+colRef(m)+')';
}

function aggExpr(m, fn){
  if(fn==='MEDIAN'){
    var expr = isAlreadyNumeric(m) ? colRef(m) : 'money('+colRef(m)+')';
    return 'PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY '+expr+')';
  }
  if(isAlreadyNumeric(m)) return fn+'('+colRef(m)+')';
  return fn+'(money('+colRef(m)+'))';
}

function escSql(s){ return String(s).replace(/'/g,"''"); }

// ── Derived sub-aggregate CTE templates ─────────────────────────
// These produce one row per BN so downstream LEFT JOINs are 1:1 with charity_base.

const GIFT_AGG_CTE =
  'gift_agg AS (\n' +
  '  SELECT g."BN/Registration number" AS bn,\n' +
  '         SUM(money(g."Total amount gifts")) AS total_gifts,\n' +
  '         SUM(money(g."Amount of gifts in kind")) AS total_gifts_in_kind,\n' +
  '         COUNT(*) AS num_donees,\n' +
  '         SUM(money(g."Political Activities Gift Amount")) AS total_political_gifts\n' +
  '  FROM gift g\n' +
  '  WHERE g.data_year = (SELECT MAX(data_year) FROM gift)\n' +
  '  GROUP BY g."BN/Registration number"\n' +
  ')';

// Trustee table column uses a straight ASCII apostrophe ("At arm's length").
// We escape it inside the single-quoted JS string with \' so the emitted SQL
// has the bare apostrophe inside a double-quoted Postgres identifier.
const TRUSTEE_AGG_CTE =
  'trustee_agg AS (\n' +
  '  SELECT t."BN/Registration number" AS bn,\n' +
  '         COUNT(*) AS num_trustees,\n' +
  '         SUM(CASE WHEN UPPER(LEFT(t."At arm\'s length", 1)) = \'Y\' THEN 1 ELSE 0 END) AS num_arm_trustees,\n' +
  '         SUM(CASE WHEN UPPER(LEFT(t."At arm\'s length", 1)) = \'N\' THEN 1 ELSE 0 END) AS num_non_arm_trustees\n' +
  '  FROM trustee t\n' +
  '  WHERE t.data_year = (SELECT MAX(data_year) FROM trustee)\n' +
  '  GROUP BY t."BN/Registration number"\n' +
  ')';

const PROGRAM_AGG_CTE =
  'program_agg AS (\n' +
  '  SELECT p."BN/Registration number" AS bn,\n' +
  '         COUNT(*) AS num_programs,\n' +
  '         SUM(CASE WHEN p."Program type OP=ongoing program, NP=new program, NA=not active" = \'OP\' THEN 1 ELSE 0 END) AS num_ongoing_programs,\n' +
  '         SUM(CASE WHEN p."Program type OP=ongoing program, NP=new program, NA=not active" = \'NP\' THEN 1 ELSE 0 END) AS num_new_programs,\n' +
  '         SUM(CASE WHEN p."Program type OP=ongoing program, NP=new program, NA=not active" = \'NA\' THEN 1 ELSE 0 END) AS num_inactive_programs\n' +
  '  FROM programs p\n' +
  '  WHERE p.data_year = (SELECT MAX(data_year) FROM programs)\n' +
  '  GROUP BY p."BN/Registration number"\n' +
  ')';

// ── SQL generation ──────────────────────────────────────────────
function genSQL(state, catalog){
  catalog = catalog || M;
  const sel = state.metrics.map(function(id){return getMetric(id,catalog);}).filter(Boolean);
  if(!sel.length) return '-- Select at least one metric';

  const uses = {
    fd:   needsTable(state,'fd',catalog),
    sc:   needsTable(state,'sc',catalog),
    cc:   needsTable(state,'cc',catalog),
    s5:   needsTable(state,'s5',catalog),
    gagg: needsTable(state,'gagg',catalog),
    tagg: needsTable(state,'tagg',catalog),
    pagg: needsTable(state,'pagg',catalog),
  };

  const ctes = [];
  if(uses.gagg) ctes.push(GIFT_AGG_CTE);
  if(uses.tagg) ctes.push(TRUSTEE_AGG_CTE);
  if(uses.pagg) ctes.push(PROGRAM_AGG_CTE);

  let q = '';
  if(ctes.length) q += 'WITH ' + ctes.join(',\n') + '\n';

  if(state.mode === 'detail'){
    q += 'SELECT\n  cb.bn,\n  cb.legal_name,\n  cb.designation_desc,\n  cb.province';
    sel.forEach(function(m){ q += ',\n  ' + moneyExpr(m) + ' AS ' + m.id; });
    q += '\n';
  } else {
    const gc = state.gb === 'designation' ? 'cb.designation_desc'
             : state.gb === 'province'    ? 'cb.province'
             : 'cb.category_desc';
    q += 'SELECT\n  ' + gc + ',\n  COUNT(*) AS charity_count';
    sel.forEach(function(m){ q += ',\n  ' + aggExpr(m, state.aggfn) + ' AS ' + m.id; });
    q += '\n';
  }

  q += 'FROM charity_base cb\n';
  if(uses.fd)   q += 'LEFT JOIN financial_d fd ON fd."BN/Registration Number" = cb.bn\n';
  if(uses.sc)   q += 'LEFT JOIN schedule_3_compensation sc ON sc."BN/Registration number" = cb.bn\n';
  if(uses.cc)   q += 'LEFT JOIN charity_counts cc ON cc.bn = cb.bn\n';
  if(uses.s5)   q += 'LEFT JOIN schedule_5_noncash s5 ON s5."BN/Registration number" = cb.bn\n';
  if(uses.gagg) q += 'LEFT JOIN gift_agg gagg ON gagg.bn = cb.bn\n';
  if(uses.tagg) q += 'LEFT JOIN trustee_agg tagg ON tagg.bn = cb.bn\n';
  if(uses.pagg) q += 'LEFT JOIN program_agg pagg ON pagg.bn = cb.bn\n';

  const w = [];
  if(state.prov)  w.push("cb.province = '"+state.prov+"'");
  if(state.desig) w.push("cb.designation_code = '"+state.desig+"'");
  if(state.cat)   w.push("cb.category_code = '"+escSql(state.cat)+"'");
  if(state.search && state.search.trim()){
    const term = escSql(state.search.trim());
    w.push("(cb.legal_name ILIKE '%"+term+"%' OR cb.bn ILIKE '%"+term+"%')");
  }
  state.filters.forEach(function(f){
    const m = getMetric(f.f, catalog);
    if(!m || !f.v) return;
    const e = isAlreadyNumeric(m) ? colRef(m) : 'money('+colRef(m)+')';
    w.push(e+' '+f.op+' '+f.v);
  });
  if(state.customWhere && state.customWhere.trim()) w.push('('+state.customWhere.trim()+')');
  if(w.length) q += 'WHERE ' + w.join('\n  AND ') + '\n';

  if(state.mode === 'aggregate'){
    const gc2 = state.gb === 'designation' ? 'cb.designation_desc'
              : state.gb === 'province'    ? 'cb.province'
              : 'cb.category_desc';
    q += 'GROUP BY ' + gc2 + '\n';
  }

  const sm = getMetric(state.sort, catalog);
  if(sm){
    const se = state.mode === 'aggregate' ? state.sort : moneyExpr(sm);
    q += 'ORDER BY ' + se + ' ' + state.dir + ' NULLS LAST\n';
  } else if(state.sort === 'charity_count' && state.mode === 'aggregate'){
    q += 'ORDER BY charity_count ' + state.dir + '\n';
  }
  q += 'LIMIT ' + state.lim + ';';
  return q;
}

// ── Number formatting ───────────────────────────────────────────
// `t` is the metric's type marker: '$' for currency, 'i' for integer, undefined → guess.
function formatValue(val, t){
  if(val === null || val === undefined || val === '') return '—';
  if(typeof val === 'number'){
    if(t === '$'){
      const sign = val < 0 ? '-' : '';
      return sign + '$' + Math.abs(Math.round(val)).toLocaleString('en-CA');
    }
    if(t === 'i'){
      return Math.round(val).toLocaleString('en-CA');
    }
    if(Math.abs(val) >= 1 || val === 0){
      return val.toLocaleString('en-CA', {maximumFractionDigits:0});
    }
    return val.toLocaleString('en-CA', {maximumFractionDigits:2});
  }
  return String(val);
}

// Build a lookup: columnName (alias used in SQL) -> metric so the table renderer
// can apply $ vs integer formatting.
function columnTypeMap(metrics, catalog){
  catalog = catalog || M;
  const map = {};
  metrics.forEach(function(id){
    const m = getMetric(id, catalog);
    if(m) map[id] = m.t;
  });
  return map;
}

const Explorer = {
  M: M,
  PRESETS: PRESETS,
  getMetric: getMetric,
  needsTable: needsTable,
  genSQL: genSQL,
  formatValue: formatValue,
  columnTypeMap: columnTypeMap,
  escSql: escSql,
};

// Browser: expose as a global so the inline classic <script> in index.html
// can still reach M, PRESETS, genSQL, etc. without becoming a module itself.
if (typeof globalThis !== 'undefined') {
  globalThis.Explorer = Explorer;
}

export { M, PRESETS, getMetric, needsTable, genSQL, formatValue, columnTypeMap, escSql };
export default Explorer;
