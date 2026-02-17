# AI Context Build — Design Document

**Date:** 2026-02-17
**Status:** Approved

## Goal

Download Blumbergs publications (PDFs) from canadiancharitylaw.ca, extract their content, and synthesize into structured context documents optimized for AI consumption. Then add project infrastructure (requirements.txt, validation script, CLAUDE.md updates).

## Why

The T3010 data has nuances that can't be learned from schema alone — field interpretation rules, form version changes, common misreporting patterns, historical baselines, and regulatory context. The Blumbergs Snapshot series (2010–2023) encodes 14 years of this knowledge. Distilling it into structured docs means future Claude sessions start with expert-level understanding.

## Publications to Download

### Sector-wide Snapshots (~14 PDFs)
Blog posts at canadiancharitylaw.ca/blog/blumbergs-*-snapshot-*/ and blumbergs_canadian_charity_sector_snapshot_*/
- Years: 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023

### Provincial Snapshots (~25 PDFs)
- Ontario: 2011, 2012, 2014, 2015, 2018, 2019, 2020, 2021, 2022
- Manitoba: 2022, 2023
- Alberta: 2012, 2018, 2022
- BC: 2012, 2018, 2021, 2022
- Quebec: 2018, 2021, 2022
- Atlantic: 2021, 2022
- Nova Scotia: 2018

### Designation Snapshots (~2 PDFs)
- 2021, 2022 (Charitable Orgs, Public/Private Foundations)

### DAF Reports (~2 PDFs)
- 2023 preliminary, 2024 full

### Pre-Budget Submissions (~5 PDFs)
- 2021, 2022, 2023, 2024, 2025

### Other (~5 PDFs)
- Political Activities Snapshot 2013
- Disbursement Quota submission
- Finance Committee submissions
- COVID impact series

**Total estimated: ~50-60 PDFs**

## Output: Structured Context Documents

### docs/context/data-interpretation-guide.md
How to correctly interpret T3010 fields:
- Revenue classification rules
- Expenditure categorization
- Common errors and misreporting patterns
- Year-over-year field changes (form version impacts)
- What each designation code means in practice (not just the label)

### docs/context/sector-trends.md
Historical baselines from 14 years of data:
- Key metrics tracked 2010-2023
- Notable shifts (COVID, DAF growth, government funding)
- Expectations for sanity-checking new data

### docs/context/methodology-notes.md
How Snapshots are built:
- Inclusion/exclusion criteria
- Aggregation handling for missing data
- Known data quality issues and workarounds
- Provincial breakdown methodology

### docs/context/regulatory-context.md
Rules that explain data patterns:
- Disbursement quota rules (and 2023 changes)
- DAF reporting requirements
- Foreign activity reporting
- Political activity limits

### Enhanced MEMORY.md
Key patterns as single-line references for always-loaded context.

## Infrastructure Additions

### requirements.txt
Pin: duckdb==1.4.4, openpyxl, pymupdf

### scripts/validate_db.py
Post-load integrity checks:
- Row count assertions
- Schema validation
- Referential integrity
- Currency field spot-checks
- Cross-table consistency

### CLAUDE.md Updates
- Reference new context docs
- Add validation script to common commands

## Process

1. Visit each blog post URL, extract PDF download links
2. Download all PDFs via wget/curl
3. Extract text from each PDF using pymupdf
4. Read and synthesize into the four context documents
5. Update MEMORY.md with key single-line patterns
6. Create requirements.txt, validate_db.py
7. Update CLAUDE.md
8. Git commit
