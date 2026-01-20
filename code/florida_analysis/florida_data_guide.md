# Florida Property Tax Data Guide

## TODOs

- [x] **Write download script**: `download_nal_files.py` downloads all 67 county NAL files for a given year.
- [x] **Download millage rates**: `download_millage_pdfs.py` downloads Table 1 PDFs for all counties, 2008-2024.
- [x] **Request historical data**: Requested 2002-2023 NAL files from PTOTechnology@floridarevenue.com (January 2026).

---

## Data Request Form

To request historical data (pre-current year): https://floridarevenue.com/property/Pages/DataPortal_RequestAssessmentRollGISData.aspx

---

Florida Department of Revenue provides statewide parcel-level property tax data. This is unusually complete—most states don't aggregate assessor data at the state level.

## Available Files

### 1. Name-Address-Legal (NAL) Files
Real property records. 165 columns including:

**Identifiers:**
- CO_NO: County number (1-67)
- PARCEL_ID: Parcel identifier
- ASMNT_YR: Assessment year

**Values:**
- JV: Just value (market value)
- AV_SD, AV_NSD: Assessed value (school district, non-school district)
- TV_SD: Taxable value for school district (additional $25k homestead exemption does NOT apply)
- TV_NSD: Taxable value for non-school/county (only municipal exemptions don't apply)
- JV_HMSTD, AV_HMSTD: Homestead values
- LND_VAL: Land value

**Exemptions (EXMPT_01 through EXMPT_82):**
Key fields for senior analysis:
- **EXMPT_03**: County-determined additional exemption for low-income seniors 65+. Up to $50,000. Applies to county taxes only.
- **EXMPT_04**: Municipality-determined additional exemption for low-income seniors 65+. Up to $50,000. Applies to municipal taxes only.

**Income eligibility rules:**
- Base threshold: $20,000 household income (set in statute)
- Adjusted annually by **national CPI** starting Jan 1, 2001
- Current threshold (2025): **$37,694**
- Same threshold statewide—does NOT vary by local COL
- Exemption amount set by local ordinance (county or municipality)

**Identification idea:** The income threshold is national, but cost of living varies locally. In low-COL areas, $37k is comfortable—seniors who are "doing fine" still qualify. In high-COL areas, $37k is struggling—only genuinely poor seniors qualify. So **low-COL areas have effectively more generous eligibility**. Cross-sectional variation in real eligibility stringency; time-series variation if local COL diverges from national CPI.

**Owner info:**
- OWN_NAME, OWN_ADDR1, OWN_CITY, OWN_STATE, OWN_ZIPCD

**Property location:**
- PHY_ADDR1, PHY_CITY, PHY_ZIPCD

### 2. Sales Data Files (SDF)
Arms-length transactions. 2009 to current.

### 3. Name-Address-Personal (NAP) Files
Tangible personal property. Less relevant for this project.

### 4. GIS Files
Parcel boundaries. 2005 to current.

## Why Florida is Promising

1. **Parcel-level exemption data**: Can observe which properties claim senior exemptions, not just jurisdiction-level policy.

2. **Local variation**: Counties and municipalities set their own additional senior exemptions (EXMPT_03, EXMPT_04). Cross-sectional and potentially time-series variation.

3. **State aggregation**: Don't need to FOIA 67 counties separately—DOR compiles statewide.

4. **The inversion trick**: Instead of collecting exemption policies from statutes, infer them from claimed values. The distribution of EXMPT_03 in a county reveals:
   - Maximum exemption amount (from the cap of claimed values)
   - Take-up rates (share of eligible parcels claiming)
   - Policy changes over time (if panel available)

## Data Availability

**Current year**: Publicly posted at the Tax Roll File Directory.

Data portal: https://floridarevenue.com/property/dataportal/

NAL files URL pattern:
```
https://floridarevenue.com/property/dataportal/Pages/default.aspx?path=/property/dataportal/Documents/PTO%20Data%20Portal/Tax%20Roll%20Data%20Files/NAL/{YEAR}{TYPE}
```
Where `{YEAR}` = 2025, 2024, etc. and `{TYPE}` = F (Final) or P (Preliminary).

Filename pattern: `NAL{COUNTY_CODE}F{YYYYMM}.csv` (e.g., NAL23F202501.csv = Miami-Dade, Final, Jan 2025)

**Millage rates** (separate from NAL files):

County Municipal Reports → Table 1-Comparison of Levies (NOT "Distribution of Taxes")

URL pattern:
```
.../County%20Municipal%20Reports/Table%201-Comparison%20of%20Levies/{YY}table1
```
Where `{YY}` = 08, 09, ..., 24 (years 2008-2024)

Then pick county from that directory. **Files are PDFs** (will need parsing).

17 years × 67 counties = ~1,100 PDFs for full panel.

Example: `/Users/jeffreyohl/Dropbox/PropertyTax/raw_data/florida_data/MillageRates/2024/Miami-Dade Table 1 (1).pdf`

PDF structure (clean tabular format, likely converted from Excel):
- Taxing Authority (matches PHY_CITY in NAL)
- Prior year millage rate + taxes levied
- Current year rolled-back rate + taxes levied
- Current year adopted millage rate + taxes levied
- % change from prior year

Includes both county-level entities (BCC, Fire/Rescue, Library, UMSA) and all municipalities.

**Note:** Some municipalities have sub-districts with separate millage (e.g., "Normandy Shores" under "City of Miami Beach"). These are special assessment areas affecting few parcels—ignore for main analysis.

Should parse easily with `pdfplumber` or `tabula-py`.

Needed to compute actual tax liability: Tax = Taxable Value × Millage Rate

**Historical years** (requires request, not formal FOIA):
- NAL and NAP files: **2002 to current** (22+ year panel)
- Sales files: 2009 to current
- GIS files: 2005 to current

### How to Request Historical Data

**Request form**: https://floridarevenue.com/property/Pages/DataPortal_RequestAssessmentRollGISData.aspx

**Or email** PTOTechnology@floridarevenue.com with:
- Year(s)
- County/counties (or "all")
- File type (NAL, NAP, SDF, GIS)

**Phone**: 850-717-6570

Files <10MB emailed directly; larger files via temporary download link.

## Sample Data

Miami-Dade (county 23) 2025 Final: 933,533 parcels, ~500MB uncompressed.

Location: `/Users/jeffreyohl/Dropbox/PropertyTax/raw_data/florida_data/Assessor/2025/NAL23F202501.csv`
