// Smoke-test the SQL the explorer generates by writing each query to a file
// so a separate DuckDB Python script can execute it. Run:
//   node tests/sql_smoke.mjs > /tmp/explorer_queries.json
//   python3 tests/sql_smoke.py
import * as Explorer from '../public/explorer.js';

const cases = [
  {name:'gifts',    state:{metrics:['tax_receipted','gifts_charities','ten_year_gifts_in','non_receipted','gifts_to_qds','grants_non_qds','noncash_total']}},
  {name:'trustees', state:{metrics:['num_trustees','num_arm_trustees','num_non_arm_trustees']}},
  {name:'programs', state:{metrics:['num_programs','num_ongoing_programs','num_new_programs','num_inactive_programs']}},
  {name:'sch6',     state:{metrics:['gift_total_amount','gift_in_kind','gift_donee_count','gift_political']}},
  {name:'mixed',    state:{mode:'aggregate', gb:'province', metrics:['total_revenue','num_trustees','num_programs','gift_total_amount']}},
];

const base = {mode:'detail',prov:'',desig:'',cat:'',gb:'designation',aggfn:'SUM',
              metrics:[],filters:[],sort:'',dir:'DESC',lim:5,search:'',customWhere:''};

const out = cases.map(c => {
  const s = Object.assign({}, base, c.state);
  if(!s.sort) s.sort = s.metrics[0];
  return {name: c.name, sql: Explorer.genSQL(s)};
});

console.log(JSON.stringify(out, null, 2));
