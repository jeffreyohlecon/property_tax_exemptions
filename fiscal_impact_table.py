"""
Generate the fiscal impact table from Census Bureau State & Local Government Finance data.

This script reads 21slsstab1.xlsx and calculates:
1. Local government revenue per capita
2. Local government expenditure per capita and per pupil (for education)
3. Local-only funded amounts (netting out state/federal transfers pro-rata)

Data source: U.S. Census Bureau, 2021 Annual Survey of State and Local Government Finances
https://www.census.gov/programs-surveys/gov-finances.html

See README in this file for data structure details.
"""

import pandas as pd

# ============================================================================
# EXTERNAL DATA (not in the Census file)
# ============================================================================
# From Census Bureau population estimates (2021)
US_POPULATION_2021 = 331_900_000

# From NCES Digest of Education Statistics (Fall 2021)
# Public K-12 enrollment
K12_ENROLLMENT_2021 = 49_400_000

# K-12 education funding by source (NCES, pre-COVID baseline)
# Source: NCES Digest of Education Statistics, Table 235.10
# "Revenues for public elementary and secondary schools, by source of funds"
# https://nces.ed.gov/programs/digest/d22/tables/dt22_235.10.asp
# Pre-pandemic average (2018-19): Local 45.3%, State 46.8%, Federal 7.8%
# Note: FY2021 had elevated federal share (~13%) due to COVID relief (CARES, CRRSA, ARP)
# We use pre-COVID shares as more representative of typical local burden
K12_LOCAL_SHARE = 0.45  # 45% of K-12 spending funded by local sources

# Number of US households (2021)
# Source: Census Bureau, Current Population Survey, Annual Social and Economic Supplement
# https://www.census.gov/data/tables/2021/demo/families/cps-2021.html
US_HOUSEHOLDS_2021 = 129_900_000

# Property tax effective rate assumption
EFFECTIVE_PROPERTY_TAX_RATE = 0.02

# Assumed home value for illustration
ASSESSED_HOME_VALUE = 350_000


def load_census_data(filepath='data/21slsstab1.xlsx'):
    """Load and parse the Census state/local finance data."""
    df = pd.read_excel(filepath, sheet_name='2021_US_WY', header=None)
    return df


def extract_value(df, row_idx, col_idx=5):
    """
    Extract a numeric value from the dataframe.

    Column indices for US data:
        2 = US Total State+Local
        4 = State only
        5 = Local only

    Values are in thousands of dollars.
    """
    val = df.iloc[row_idx, col_idx]
    if pd.isna(val):
        return 0
    return float(val) * 1000  # Convert from thousands to dollars


def build_data_dict(df):
    """
    Extract all relevant fiscal data from the Census spreadsheet.
    Returns dict with values in actual dollars (not thousands).

    Row indices based on file structure:
        Row 20: Intergovernmental Revenue (total)
        Row 21: From Federal Government
        Row 22: From State Government
        Row 25: General Revenue from Own Sources
        Row 26: Taxes (total)
        Row 27: Property Tax
        Row 28: Sales and Gross Receipts
        Row 41: Charges and Miscellaneous General Revenue
        Row 82: Direct Expenditure
        Row 93: Direct General Expenditure
        Row 98: Education (total)
        Row 100: Higher Education
        Row 102: Elementary & Secondary Education
    """
    data = {}

    # === REVENUE ===
    # Property tax (local)
    data['property_tax'] = extract_value(df, 27, col_idx=5)

    # Sales and gross receipts (local)
    data['sales_tax'] = extract_value(df, 28, col_idx=5)

    # Charges and miscellaneous general revenue (local)
    data['charges_fees'] = extract_value(df, 41, col_idx=5)

    # Total taxes (local)
    data['total_taxes'] = extract_value(df, 26, col_idx=5)

    # General revenue from own sources (local)
    data['local_own_source_revenue'] = extract_value(df, 25, col_idx=5)

    # Non-property tax revenue = Sales + Charges + Other taxes
    # Other taxes = Total taxes - Property - Sales
    other_taxes = data['total_taxes'] - data['property_tax'] - data['sales_tax']
    data['non_property_revenue'] = data['sales_tax'] + data['charges_fees'] + other_taxes

    # === INTERGOVERNMENTAL REVENUE RECEIVED BY LOCAL ===
    data['local_from_federal'] = extract_value(df, 21, col_idx=5)
    data['local_from_state'] = extract_value(df, 22, col_idx=5)
    data['local_intergovernmental'] = data['local_from_federal'] + data['local_from_state']

    # === EXPENDITURE ===
    # Direct expenditure (local) - total
    data['local_direct_expenditure'] = extract_value(df, 82, col_idx=5)

    # Direct general expenditure (local)
    data['local_direct_general_expenditure'] = extract_value(df, 93, col_idx=5)

    # Elementary & secondary education (local)
    data['local_k12_expenditure'] = extract_value(df, 102, col_idx=5)

    # Higher education (local)
    data['local_higher_ed'] = extract_value(df, 100, col_idx=5)

    # Total education (local)
    data['local_total_education'] = extract_value(df, 98, col_idx=5)

    # Non-education local direct general expenditure
    # = Direct General - E&S - Higher Ed
    data['local_non_education_expenditure'] = (
        data['local_direct_general_expenditure']
        - data['local_k12_expenditure']
        - data['local_higher_ed']
    )

    return data


def calculate_local_funded_shares(data):
    """
    Calculate the share of local expenditure funded by local sources only
    (i.e., netting out state and federal transfers).

    We use NCES data for K-12 (45% local) and back-calculate the implied
    local share for non-education services.

    Logic: Total_transfers = K12_transfers + Other_transfers
           If K-12 is 45% local-funded, then 55% comes from transfers.
           Remaining transfers go to non-education services.

    Returns dict with 'k12' and 'other' local shares.
    """
    total_transfers = data['local_intergovernmental']
    total_expenditure = data['local_direct_expenditure']

    # Overall pro-rata local share (for reference)
    overall_local_share = 1 - (total_transfers / total_expenditure)

    # K-12 local share from NCES
    k12_local_share = K12_LOCAL_SHARE  # 0.45

    # K-12 expenditure and implied transfers
    k12_expenditure = data['local_k12_expenditure']
    k12_transfers = k12_expenditure * (1 - k12_local_share)  # 55% from transfers

    # Non-education expenditure and transfers
    # Note: we include higher ed with "other" since we don't have specific share data
    other_expenditure = total_expenditure - k12_expenditure
    other_transfers = total_transfers - k12_transfers

    # Back-calculated local share for non-education
    other_local_share = 1 - (other_transfers / other_expenditure)

    return {
        'overall': overall_local_share,
        'k12': k12_local_share,
        'other': other_local_share,
        'k12_transfers': k12_transfers,
        'other_transfers': other_transfers,
    }


def generate_table_values(data, population=US_POPULATION_2021, enrollment=K12_ENROLLMENT_2021,
                          households=US_HOUSEHOLDS_2021):
    """
    Generate all values needed for the fiscal impact table.

    Revenue is per capita (consumption-based: more people = more sales tax, fees, etc.)
    Other local services are per household (police, fire, roads, sewerage serve households)
    """
    results = {}

    # Calculate local-funded shares for K-12 and other services
    shares = calculate_local_funded_shares(data)
    results['local_shares'] = shares
    results['k12_local_share'] = shares['k12']
    results['other_local_share'] = shares['other']

    # === REVENUE ===
    # Non-property local own-source revenue per capita
    # Rationale: Sales tax, charges, and fees are consumption-based (more people = more spending)
    results['non_property_revenue_total'] = data['non_property_revenue']
    results['non_property_revenue_per_capita'] = data['non_property_revenue'] / population

    # Property tax (calculated from assumed home value)
    results['property_tax_per_home'] = ASSESSED_HOME_VALUE * EFFECTIVE_PROPERTY_TAX_RATE

    # === EXPENDITURE: GROSS (before netting transfers) ===
    results['k12_per_pupil_gross'] = data['local_k12_expenditure'] / enrollment
    results['other_services_per_capita_gross'] = data['local_non_education_expenditure'] / population
    results['other_services_per_household_gross'] = data['local_non_education_expenditure'] / households

    # === EXPENDITURE: LOCAL-ONLY ===
    # K-12: Use NCES local share (45%) - more accurate than pro-rata
    results['k12_per_pupil_local_only'] = (
        data['local_k12_expenditure'] * K12_LOCAL_SHARE
    ) / enrollment

    # Other services: per household, with back-calculated local share
    # Rationale: Police, fire, roads, sewerage, trash primarily serve households
    # (a 2-person household uses similar services as a 4-person household)
    results['other_services_per_household_local_only'] = (
        data['local_non_education_expenditure'] * shares['other']
    ) / households

    # Keep per-capita for reference
    results['other_services_per_capita_local_only'] = (
        data['local_non_education_expenditure'] * shares['other']
    ) / population

    # Store raw data for reference
    results['raw_data'] = data

    return results


def format_currency(val, include_cents=False):
    """Format a number as currency."""
    if include_cents:
        return f"${val:,.2f}"
    return f"${val:,.0f}"


def print_summary(results):
    """Print a summary of the calculations."""
    data = results['raw_data']

    print("=" * 70)
    print("FISCAL IMPACT TABLE - CALCULATED VALUES")
    print("=" * 70)
    print(f"\nData source: U.S. Census Bureau, 2021 Annual Survey of State & Local")
    print(f"Population: {US_POPULATION_2021:,}")
    print(f"Households: {US_HOUSEHOLDS_2021:,}")
    print(f"K-12 Enrollment: {K12_ENROLLMENT_2021:,}")

    print(f"\n--- RAW DATA FROM CENSUS (billions) ---")
    print(f"Local K-12 expenditure: ${data['local_k12_expenditure']/1e9:.1f}B")
    print(f"Local higher ed: ${data['local_higher_ed']/1e9:.1f}B")
    print(f"Local direct general expenditure: ${data['local_direct_general_expenditure']/1e9:.1f}B")
    print(f"Local non-education expenditure: ${data['local_non_education_expenditure']/1e9:.1f}B")
    print(f"Local intergovernmental from state: ${data['local_from_state']/1e9:.1f}B")
    print(f"Local intergovernmental from federal: ${data['local_from_federal']/1e9:.1f}B")
    print(f"Local direct expenditure (total): ${data['local_direct_expenditure']/1e9:.1f}B")

    shares = results['local_shares']
    print(f"\n--- LOCAL FUNDING SHARES ---")
    print(f"Overall (pro-rata): {shares['overall']:.1%}")
    print(f"K-12 education (NCES): {shares['k12']:.0%}")
    print(f"Other services (back-calculated): {shares['other']:.1%}")
    print(f"  Logic: Total transfers ${data['local_intergovernmental']/1e9:.0f}B = "
          f"K-12 transfers ${shares['k12_transfers']/1e9:.0f}B + "
          f"Other ${shares['other_transfers']/1e9:.0f}B")

    print(f"\n--- REVENUE (per capita) ---")
    print(f"Property tax (2% on $350K home): {format_currency(results['property_tax_per_home'])}")
    print(f"Sales tax & other per capita: {format_currency(results['non_property_revenue_per_capita'])}")
    print(f"  (Total non-property revenue: ${results['non_property_revenue_total']/1e9:.1f}B)")

    print(f"\n--- EXPENDITURE: GROSS (before netting transfers) ---")
    print(f"K-12 education per pupil: {format_currency(results['k12_per_pupil_gross'])}")
    print(f"Other local services per household: {format_currency(results['other_services_per_household_gross'])}")
    print(f"  (per capita: {format_currency(results['other_services_per_capita_gross'])})")

    print(f"\n--- EXPENDITURE: LOCAL-ONLY ---")
    print(f"K-12 education per pupil ({shares['k12']:.0%} local): {format_currency(results['k12_per_pupil_local_only'])}")
    print(f"Other services per household ({shares['other']:.0%} local): {format_currency(results['other_services_per_household_local_only'])}")
    print(f"  (per capita: {format_currency(results['other_services_per_capita_local_only'])})")


def generate_latex_table(results, use_local_only=True):
    """
    Generate LaTeX table code for the fiscal impact comparison.

    use_local_only: If True, uses local-funded-only values (nets out transfers).
                    If False, uses gross expenditure values.

    Revenue: per capita (consumption-based)
    Education: per pupil
    Other services: per household (police, fire, roads serve households not individuals)
    """
    data = results['raw_data']

    # Choose which expenditure values to use
    shares = results['local_shares']
    if use_local_only:
        k12_per_pupil = results['k12_per_pupil_local_only']
        other_per_hh = results['other_services_per_household_local_only']
        method_note = (
            f"Education expenditure reflects local-funded share only ({shares['k12']*100:.0f}\\%, per NCES). "
            f"For other services, we allocate {100-shares['k12']*100:.0f}\\% of K--12 spending to state/federal transfers "
            f"(\\${shares['k12_transfers']/1e9:.0f}B), leaving \\${shares['other_transfers']/1e9:.0f}B for non-education---"
            f"implying a {shares['other']*100:.0f}\\% local share."
        )
    else:
        k12_per_pupil = results['k12_per_pupil_gross']
        other_per_hh = results['other_services_per_household_gross']
        method_note = (
            "Expenditure figures reflect total local government spending, including amounts "
            "funded by state and federal transfers."
        )

    # Revenue values
    prop_tax = results['property_tax_per_home']
    other_rev_per_cap = results['non_property_revenue_per_capita']

    # Household calculations
    # 70-year couple: 2 adults, 0 children, 1 household
    couple_other_rev = other_rev_per_cap * 2
    couple_total_rev = prop_tax + couple_other_rev
    couple_k12_cost = 0
    couple_other_cost = other_per_hh * 1  # 1 household
    couple_total_cost = couple_k12_cost + couple_other_cost
    couple_surplus = couple_total_rev - couple_total_cost

    # Family of 4: 2 adults, 2 children (K-12), 1 household
    family_other_rev = other_rev_per_cap * 4
    family_total_rev = prop_tax + family_other_rev
    family_k12_cost = k12_per_pupil * 2
    family_other_cost = other_per_hh * 1  # 1 household
    family_total_cost = family_k12_cost + family_other_cost
    family_surplus = family_total_rev - family_total_cost

    # Format numbers
    def fmt(x):
        return f"\\${x:,.0f}"

    def fmt_surplus(x):
        if x >= 0:
            return f"+\\${x:,.0f}"
        else:
            return f"(\\${abs(x):,.0f})"

    # Build caption
    non_prop_b = results['non_property_revenue_total'] / 1e9
    k12_b = data['local_k12_expenditure'] / 1e9
    non_ed_b = data['local_non_education_expenditure'] / 1e9
    pop_m = US_POPULATION_2021 / 1e6
    hh_m = US_HOUSEHOLDS_2021 / 1e6
    enroll_m = K12_ENROLLMENT_2021 / 1e6

    caption = (
        f"Illustrative marginal fiscal impact of new residents on local government. "
        f"\\textit{{Revenue}}: Property tax assumes 2\\% effective rate on assessed value. "
        f"Sales tax \\& other includes local sales taxes, charges, and fees "
        f"(\\${other_rev_per_cap:,.0f}/capita = \\${non_prop_b:.0f}B total non-property "
        f"local own-source revenue $\\div$ {pop_m:.1f}M population). "
        f"\\textit{{Expenditure}}: Education calculated as local direct expenditure on "
        f"elementary and secondary education (\\${k12_b:.0f}B) divided by public K--12 "
        f"enrollment ({enroll_m:.1f}M students). Other local services calculated as "
        f"local direct general expenditure excluding education (\\${non_ed_b:.0f}B) divided "
        f"by {hh_m:.1f}M households, covering police, fire, roads, sewerage, parks, courts, "
        f"and administration---services that primarily serve households rather than individuals. "
        f"{method_note} "
        f"Source: U.S. Census Bureau, 2021 Annual Survey of State and Local Government Finances; "
        f"population and households from Census Bureau; enrollment from NCES."
    )

    latex = f"""\\begin{{table}}[htbp!]
    \\centering
    \\small
    \\begin{{tabular}}{{|l|r|r|r|}}
    \\hline
    \\textbf{{Line Item}} & \\textbf{{Per Unit}} & \\textbf{{70-Yr Couple}} & \\textbf{{Family of 4}} \\\\ \\hline
    \\multicolumn{{4}}{{|c|}}{{\\textit{{Assumptions}}}} \\\\ \\hline
    Household Composition & --- & 2 Adults (65+) & 2 Adults, 2 Children \\\\ \\hline
    Assessed Home Value & --- & \\$350,000 & \\$350,000 \\\\ \\hline
    \\multicolumn{{4}}{{|c|}}{{\\textit{{Revenue Generated}}}} \\\\ \\hline
    Property Tax (2\\% effective) & --- & {fmt(prop_tax)} & {fmt(prop_tax)} \\\\ \\hline
    Sales Tax \\& Other & {fmt(other_rev_per_cap)}/capita & {fmt(couple_other_rev)} & {fmt(family_other_rev)} \\\\ \\hline
    \\textbf{{Total Revenue}} & --- & \\textbf{{{fmt(couple_total_rev)}}} & \\textbf{{{fmt(family_total_rev)}}} \\\\ \\hline
    \\multicolumn{{4}}{{|c|}}{{\\textit{{Marginal Cost of Services}}}} \\\\ \\hline
    Public Education (K--12) & {fmt(k12_per_pupil)}/pupil & \\$0 & {fmt(family_k12_cost)} \\\\ \\hline
    Other Local Services & {fmt(other_per_hh)}/household & {fmt(couple_other_cost)} & {fmt(family_other_cost)} \\\\ \\hline
    \\textbf{{Total Marginal Cost}} & --- & \\textbf{{{fmt(couple_total_cost)}}} & \\textbf{{{fmt(family_total_cost)}}} \\\\ \\hline
    \\multicolumn{{4}}{{|c|}}{{\\textit{{Net Fiscal Impact}}}} \\\\ \\hline
    \\textbf{{Surplus / (Deficit)}} & --- & \\textbf{{{fmt_surplus(couple_surplus)}}} & \\textbf{{{fmt_surplus(family_surplus)}}} \\\\ \\hline
    \\end{{tabular}}
    \\caption{{{caption}}}
    \\label{{tab:fiscal_impact}}
\\end{{table}}"""

    return latex


def main():
    """Main function to generate the fiscal impact table."""
    # Load data
    print("Loading Census data...")
    df = load_census_data()

    # Extract relevant values
    print("Extracting fiscal data...")
    data = build_data_dict(df)

    # Calculate table values
    print("Calculating per-capita/per-pupil values...")
    results = generate_table_values(data)

    # Print summary
    print_summary(results)

    # Generate LaTeX tables (both versions)
    print("\n" + "=" * 70)
    print("LATEX TABLE (LOCAL-ONLY, netting out state/federal transfers)")
    print("=" * 70)
    latex_local = generate_latex_table(results, use_local_only=True)
    print(latex_local)

    print("\n" + "=" * 70)
    print("LATEX TABLE (GROSS, including all local expenditure)")
    print("=" * 70)
    latex_gross = generate_latex_table(results, use_local_only=False)
    print(latex_gross)

    # Save the local-only version to a file
    with open('figures/fiscal_impact_table.tex', 'w') as f:
        f.write(latex_local)
    print("\n\nSaved local-only table to figures/fiscal_impact_table.tex")

    return results


if __name__ == '__main__':
    main()
