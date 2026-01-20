# Work Log: January 20, 2026 (12:00-17:00)

## Summary

Five hours of data discovery, script writing, and strategic thinking. Started with no Florida data; ended with sample data downloaded, historical data requested, and clearer (if sobering) assessment of what the project can and cannot do.

---

## Data Discovery & Documentation (12:00-14:00)

**Discovered Florida DOR provides unusually complete statewide parcel data:**
- NAL files (Name-Address-Legal): 165 columns, 2002-present, all 67 counties
- Key fields: exemption amounts (EXMPT_03 = county senior, EXMPT_04 = municipal senior), taxable values, owner/property addresses
- Sales data: 2009-present
- Millage rates: Table 1 PDFs by county, 2008-2024

**Created:** [florida_data_guide.md](code/florida_analysis/florida_data_guide.md) documenting field meanings, URLs, and data request process.

---

## Scripts Written (13:53-14:49)

| Script | Purpose |
|--------|---------|
| `download_nal_files.py` | Downloads current-year NAL files for all 67 counties |
| `download_millage_pdfs.py` | Downloads Table 1 millage PDFs for all counties, 2008-2024 |
| `parse_millage_pdf.py` | Extracts millage rates from PDFs |
| `analyze_nal.py` | Basic NAL file analysis |

Located in: `code/florida_analysis/`

---

## Data Downloaded

**Dropbox location:** `/Users/jeffreyohl/Dropbox/PropertyTax/raw_data/florida_data/`

| Data | Size | Notes |
|------|------|-------|
| Miami-Dade NAL 2025 | ~500MB | 933,533 parcels |
| Millage PDFs | ~200 files | Multiple counties, 2022-2024 |
| Documentation | 2 PDFs | NAL user guide, field layout |

---

## Key Findings from Miami-Dade Sample

- **Senior exemption claiming:** ~35,000 parcels (3.7% of total)
- **Exemption values:** Cluster at $50k and $25k caps (policy variation visible)
- **Mean savings:** $487/year (county $360, municipal $127)
- **Revenue hole:** $11.1M/year = **0.35% of county levy**

**Critical implication:** The fiscal effect is too small to drive detectable rate responses. The spillover to non-seniors (~$7/year per $300k home) is real but buried in noise.

---

## Historical Data Request

**Emailed:** PTOTechnology@floridarevenue.com
**Requested:** NAL files 2002-2023, all counties
**Expected response:** ~5 business days

---

## Thinking/Writing (15:00-17:00)

**Created/updated:**
- [brainstorming_our_point.md](memos/ourpoint/brainstorming_our_point.md) - raw ideas
- [analysis_ideas.md](code/florida_analysis/analysis_ideas.md) - project status and findings
- [outline_our_point.tex](memos/ourpoint/outline_our_point.tex) - main working document
- [data_plan.tex](memos/data_plan/data_plan.tex) - data sources and limitations

**Key strategic conclusions:**
1. The original December question ("do exemptions raise rates for non-seniors?") likely isn't answerable with Florida data—the fiscal effect is too small.
2. Florida's income cap ($38k) rules out the fiscal-competition-for-wealthy-retirees story.
3. Two types of exemptions exist (uncapped vs. income-capped)—need a theory for why both exist.
4. The within-Florida local variation (municipalities adopt at different times/levels) is the best source of identification.

---

## Current Status

**Data:** Good microdata exists. Sample downloaded. Historical requested.

**Theory:** Don't have one.

**Candidate theories to evaluate:**
- Fiscal competition (predicts generous exemptions where migration is elastic)
- Political capture (predicts rich seniors get more—income caps inconsistent)
- Anti-displacement (predicts caps and tenure requirements)

**Possible framing:** Uncapped = attract. Capped = protect. Test: Do uncapped jurisdictions see more senior in-migration? Do capped jurisdictions see more senior stability?

**Next step:** Thinking, not data collection. Write down candidate theories and evaluate which are testable.

---

## File Tree (New/Modified Today)

```
property_tax_exemptions/
├── work_log_jan_20_2026.md          # This file
├── CLAUDE.md                         # Updated framing reminder
├── code/florida_analysis/
│   ├── download_nal_files.py
│   ├── download_millage_pdfs.py
│   ├── parse_millage_pdf.py
│   ├── analyze_nal.py
│   ├── florida_data_guide.md
│   └── analysis_ideas.md
└── memos/
    ├── data_plan/data_plan.tex
    └── ourpoint/
        ├── outline_our_point.tex
        └── brainstorming_our_point.md

Dropbox/PropertyTax/raw_data/florida_data/
├── Assessor/2025/NAL23F202501.csv   # Miami-Dade sample
├── MillageRates/                     # ~200 PDFs
└── Documentation/                    # User guides
```
