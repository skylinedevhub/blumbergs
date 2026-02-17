-- Charity Lookup: detailed profile for a single charity
-- Replace $BN with the charity's BN/Registration Number
-- Example: 119080464RR0001
--
-- Usage: python3 -c "
-- import duckdb, sys
-- bn = sys.argv[1]
-- con = duckdb.connect('data/db/cra_charities.duckdb', read_only=True)
-- sql = open('scripts/queries/charity_lookup.sql').read().replace('\$BN', bn)
-- for stmt in sql.split(';\n'):
--     stmt = stmt.strip()
--     if stmt and not stmt.startswith('--'):
--         print(con.execute(stmt).fetchdf().to_string())
--         print()
-- con.close()
-- " 119080464RR0001

-- Identity
SELECT * FROM charity_base WHERE bn = '$BN';

-- Financial summary
SELECT
    bn, fiscal_period_end,
    TRY_CAST(REPLACE(REPLACE("4700", '$', ''), ',', '') AS DECIMAL) AS total_revenue,
    TRY_CAST(REPLACE(REPLACE("5100", '$', ''), ',', '') AS DECIMAL) AS total_expenditures,
    TRY_CAST(REPLACE(REPLACE("4200", '$', ''), ',', '') AS DECIMAL) AS total_assets,
    TRY_CAST(REPLACE(REPLACE("4350", '$', ''), ',', '') AS DECIMAL) AS total_liabilities,
    TRY_CAST(REPLACE(REPLACE("4500", '$', ''), ',', '') AS DECIMAL) AS tax_receipted_gifts,
    TRY_CAST(REPLACE(REPLACE("5000", '$', ''), ',', '') AS DECIMAL) AS charitable_expenditures,
    TRY_CAST(REPLACE(REPLACE("5010", '$', ''), ',', '') AS DECIMAL) AS mgmt_admin,
    TRY_CAST(REPLACE(REPLACE("5020", '$', ''), ',', '') AS DECIMAL) AS fundraising
FROM v_financial_d
WHERE bn = '$BN';

-- Compensation
SELECT bn, fiscal_period_end, ft_employees, pt_employees, total_compensation
FROM v_compensation
WHERE bn = '$BN';

-- Programs
SELECT bn, program_type, description
FROM v_programs
WHERE bn = '$BN';

-- Grants to non-qualified donees
SELECT bn, recipient_name, purpose, cash_amount, country
FROM v_grants
WHERE bn = '$BN';

-- Foreign operations
SELECT bn, country_code
FROM v_operating_countries
WHERE bn = '$BN';

-- Subsidiary relationships
SELECT * FROM v_subsidiaries
WHERE subsidiary_bn = '$BN' OR parent_bn = '$BN'
