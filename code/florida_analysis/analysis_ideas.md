# Florida Property Tax Analysis - Project Status

> **FRAMING CHECK**: Before requesting new code/data work, articulate the contribution. See `memos/outline_our_point.md`.

## What We Have

### Data Sources Confirmed
- [x] **NAL files (parcel-level)**: 2002-present, all 67 counties
  - Exemption amounts (EXMPT_03 = county senior, EXMPT_04 = municipal senior)
  - Taxable values (TV_SD, TV_NSD) with exemptions already applied
  - Location (PHY_CITY links to municipality)
  - Current year publicly available; historical requires data request

- [x] **Millage rate PDFs**: 2008-2024, all 67 counties
  - County-level rates (BCC, Fire/Rescue, Library, UMSA)
  - Municipal rates for all cities
  - Clean tabular format, parseable with pdfplumber/tabula

### Sample Data Downloaded
- [x] Miami-Dade NAL 2025: `/Users/jeffreyohl/Dropbox/PropertyTax/raw_data/florida_data/Assessor/2025/NAL23F202501.csv`
- [x] Miami-Dade millage PDF 2024: `/Users/jeffreyohl/Dropbox/PropertyTax/raw_data/florida_data/MillageRates/2024/Miami-Dade Table 1 (1).pdf`

### Linkage Verified
- [x] PHY_CITY in NAL matches municipality names in millage PDF (with "City of " prefix)
- [x] TAX_AUTH_CD provides numeric codes for each jurisdiction
- [x] Can compute tax liability = Taxable Value × Millage Rate
- [x] Can compute exemption savings = Exemption Amount × Millage Rate

## Key Findings So Far

### Senior Exemption (EXMPT_03/04) in Miami-Dade
- ~35,000 parcels claim senior exemptions (3.7% of total)
- Exemption caps cluster at $50k and $25k (policy variation visible in data)
- 100% overlap with homestead exemption (as expected)
- County and municipal exemptions track together (34,819 have both)

### Dollar Value of Exemption (computed)
- Mean total savings: $487/year (county: $360, municipal: $127)
- Range: $0.57 to $833/year depending on location and exemption amount
- **Policy variation**: Florida City and Miami Shores do NOT offer municipal senior exemption
- High-millage cities (North Miami 7.4, Opa-Locka 9.16): up to $732/year
- Low-millage cities (Aventura 1.73, Doral 1.72): ~$360-$450/year

### Exemption Distribution (Miami-Dade 2025)

| Exemption Amount | Parcels | % of Exempted | % of All Parcels |
|------------------|---------|---------------|------------------|
| <$10k            | 338     | 1.0%          | 0.04%            |
| $10k-$25k        | 5,421   | 15.5%         | 0.58%            |
| $25k-$50k        | 29,183  | 83.5%         | 3.13%            |
| >$50k            | 0       | 0.0%          | 0.00%            |
| **Total**        | 34,942  | 100%          | 3.74%            |

Mean exemption: $43,842 | Median: $50,000 (the cap)

### Revenue Hole Assessment
- Total EXMPT_03 (county senior): $1.53B exempted from tax base
- Exemption as % of taxable base: 0.31%
- County revenue forgone: $11.1M/year
- As % of county levy: **0.35%**

**Implication**: The senior exemption creates a small revenue hole (~0.35% of county levy). This is unlikely to drive meaningful changes in millage rates. The exemption only applies to county/municipal levies—not school district or special district taxes, which are often larger components.

**Household-level significance**:
- Mean savings ($487/year) = 1.3% of income at eligibility threshold ($37,694)
- Max savings ($720/year in high-millage city) = 1.9% of income
- Comparable to a Social Security COLA adjustment—not huge, but economically meaningful for a low-income senior

**Incidence arithmetic**:
- $11M forgone spread across $488B taxable base = 0.0225 mills rate increase
- For a $300k home: ~$7/year additional tax to subsidize seniors
- Real but undetectable—buried in year-to-year rate noise

**Research framing problems**:
1. **Fiscal competition doesn't fit**: The exemption is income-limited ($37,694), so you're "competing" for low-income seniors—not the wealthy retirees in the standard fiscal competition story. Low-income seniors may be fiscal costs, not assets.
2. **Rate response too small**: 0.35% revenue hole won't produce detectable rate changes. The spillover to non-seniors (~$7/year) is real but not identifiable.
3. **Capitalization is generic**: "Who captures the incidence" is the standard public finance question—not a contribution on its own.

**What might work**:
- The COL mismatch (national income threshold vs local prices) creates cross-sectional variation in effective eligibility—but unclear what outcome to study
- Take-up patterns (who claims vs who doesn't among eligibles)—but we don't observe income
- Descriptive: document the policy variation and dollar values across Florida—useful but not causal

**Open question**: What's the research question that makes Florida interesting beyond "Florida has good data"?

### Identification Idea
Income eligibility ($37,694) is set by **national CPI**, not local COL. This creates cross-sectional variation:
- Low-COL areas: $37k is comfortable → more generous effective eligibility
- High-COL areas: $37k is struggling → stricter effective eligibility

Time-series variation if local COL diverges from national CPI.

## Next Steps

### Data Collection
- [ ] **Request historical NAL files**: Email PTOTechnology@floridarevenue.com for 2002-2023, all counties
- [ ] **Download current NAL files**: Write script to pull all 67 counties from data portal
- [ ] **Download millage PDFs**: Get Table 1-Comparison of Levies for all years/counties

### Data Processing
- [x] **Parse millage PDFs**: `parse_millage_pdf.py` extracts county + municipal rates
- [x] **Build municipality crosswalk**: Handles NAL PHY_CITY → millage PDF names (including aliases)
- [x] **Compute exemption savings**: `compute_exemption_savings()` calculates parcel-level dollar savings

### Analysis
- [x] **Map exemption value**: Dollar value of senior exemption by location (done for Miami-Dade)
- [ ] **Explore policy variation**: Which counties/cities offer $50k vs $25k caps?
- [ ] **Time series**: How have exemption values changed as millage rates change?
- [ ] **COL identification**: Relate exemption take-up to local cost of living

## File Locations

```
/Users/jeffreyohl/Dropbox/PropertyTax/raw_data/florida_data/
├── Assessor/2025/
│   └── NAL23F202501.csv          # Miami-Dade 2025
└── MillageRates/2024/
    └── Miami-Dade Table 1 (1).pdf # Miami-Dade millage rates
```

## URLs

- Data portal: https://floridarevenue.com/property/dataportal/
- Historical data request form: https://floridarevenue.com/property/Pages/DataPortal_RequestAssessmentRollGISData.aspx
- Millage PDFs: `.../County%20Municipal%20Reports/Table%201-Comparison%20of%20Levies/{YY}table1`

## Documentation

- [florida_data_guide.md](florida_data_guide.md) - Detailed field descriptions and data structure
