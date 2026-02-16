-- Sector Snapshot: Blumbergs-style aggregate statistics
-- Reproduces the kind of analysis in the Blumbergs Snapshot reports
-- Usage: python3 -c "import duckdb; con=duckdb.connect('data/db/cra_charities.duckdb',read_only=True); print(con.execute(open('scripts/queries/sector_snapshot.sql').read()).fetchdf().to_string())"

WITH financials AS (
    SELECT
        CAST(REPLACE(REPLACE("4700", '$', ''), ',', '') AS DECIMAL) AS total_revenue,
        CAST(REPLACE(REPLACE("5100", '$', ''), ',', '') AS DECIMAL) AS total_expenditures,
        CAST(REPLACE(REPLACE("4500", '$', ''), ',', '') AS DECIMAL) AS tax_receipted_gifts,
        CAST(REPLACE(REPLACE("4510", '$', ''), ',', '') AS DECIMAL) AS gifts_from_charities,
        CAST(REPLACE(REPLACE("4540", '$', ''), ',', '') AS DECIMAL) AS federal_govt,
        CAST(REPLACE(REPLACE("4550", '$', ''), ',', '') AS DECIMAL) AS provincial_govt,
        CAST(REPLACE(REPLACE("4560", '$', ''), ',', '') AS DECIMAL) AS municipal_govt,
        CAST(REPLACE(REPLACE("4200", '$', ''), ',', '') AS DECIMAL) AS total_assets,
        CAST(REPLACE(REPLACE("4350", '$', ''), ',', '') AS DECIMAL) AS total_liabilities,
        CAST(REPLACE(REPLACE("5000", '$', ''), ',', '') AS DECIMAL) AS charitable_expenditures,
        CAST(REPLACE(REPLACE("5010", '$', ''), ',', '') AS DECIMAL) AS mgmt_admin,
        CAST(REPLACE(REPLACE("5020", '$', ''), ',', '') AS DECIMAL) AS fundraising,
        CAST(REPLACE(REPLACE("5050", '$', ''), ',', '') AS DECIMAL) AS gifts_to_qd
    FROM financial_d
)
SELECT
    -- Counts
    (SELECT COUNT(*) FROM ident) AS total_charities,
    (SELECT COUNT(*) FROM charity_base WHERE designation_code = 'C') AS charitable_orgs,
    (SELECT COUNT(*) FROM charity_base WHERE designation_code = 'A') AS public_foundations,
    (SELECT COUNT(*) FROM charity_base WHERE designation_code = 'B') AS private_foundations,

    -- Revenue
    SUM(total_revenue) AS total_revenue,
    SUM(tax_receipted_gifts) AS total_tax_receipted_gifts,
    SUM(gifts_from_charities) AS total_gifts_from_charities,
    SUM(federal_govt) AS total_federal_govt,
    SUM(provincial_govt) AS total_provincial_govt,
    SUM(municipal_govt) AS total_municipal_govt,
    SUM(federal_govt) + SUM(provincial_govt) + SUM(municipal_govt) AS total_govt_revenue,

    -- Expenditures
    SUM(total_expenditures) AS total_expenditures,
    SUM(charitable_expenditures) AS total_charitable_expenditures,
    SUM(mgmt_admin) AS total_mgmt_admin,
    SUM(fundraising) AS total_fundraising,
    SUM(gifts_to_qd) AS total_gifts_to_qd,

    -- Balance sheet
    SUM(total_assets) AS total_assets,
    SUM(total_liabilities) AS total_liabilities,

    -- Activity counts
    (SELECT COUNT(DISTINCT bn) FROM v_operating_countries) AS charities_with_foreign_ops,
    (SELECT COUNT(DISTINCT bn) FROM v_grants) AS charities_making_grants,
    (SELECT COUNT(*) FROM schedule_3_compensation WHERE "390" IS NOT NULL) AS charities_with_compensation

FROM financials;
