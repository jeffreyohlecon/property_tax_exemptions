"""
NYC SCHE Coverage Erosion Analysis

Computes the share of 65+ homeowner households below the $29,000 income limit
in 2009 vs 2024 to illustrate coverage erosion from frozen income thresholds.

The NYC Senior Citizen Homeowner Exemption (SCHE) had an income limit frozen
at $29,000 from 2009-2024. This script shows how inflation eroded eligibility.
"""

import requests
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# Census API key (from existing notebook)
CENSUS_API_KEY = "488b0df48f856b207eae540095aee8cd37926d3a"
OUTPUT_DIR = 'figures'

# NYC PUMA codes (for PUMS data) - all 5 boroughs
NYC_PUMAS = [
    # Manhattan (New York County, FIPS 36061)
    '3603701', '3603702', '3603703', '3603704', '3603705',
    '3603706', '3603707', '3603708', '3603709', '3603710',
    # Bronx (Bronx County, FIPS 36005)
    '3603801', '3603802', '3603803', '3603804', '3603805',
    '3603806', '3603807', '3603808', '3603809', '3603810',
    # Brooklyn (Kings County, FIPS 36047)
    '3604001', '3604002', '3604003', '3604004', '3604005',
    '3604006', '3604007', '3604008', '3604009', '3604010',
    '3604011', '3604012', '3604013', '3604014', '3604015',
    '3604016', '3604017', '3604018',
    # Queens (Queens County, FIPS 36081)
    '3604101', '3604102', '3604103', '3604104', '3604105',
    '3604106', '3604107', '3604108', '3604109', '3604110',
    '3604111', '3604112', '3604113', '3604114',
    # Staten Island (Richmond County, FIPS 36085)
    '3603901', '3603902', '3603903',
]

# NYC county FIPS codes
NYC_COUNTIES = ['36061', '36005', '36047', '36081', '36085']


def load_puma_county_crosswalk():
    """
    Load PUMA to county crosswalk from Census.
    Returns set of NYC PUMAs for each vintage.
    """
    # Census provides crosswalk files - for now use a simple approach:
    # Download and cache, or use known mappings
    # https://www.census.gov/programs-surveys/geography/guidance/geo-areas/pumas.html

    # Fallback: return None and use direct PUMS query by place
    return None


def get_pums_data(year, use_cache=True):
    """
    Fetch ACS PUMS data for NYC 65+ homeowner households.

    Variables:
    - AGEP: Age
    - HINCP: Household income
    - TEN: Tenure (1=owned with mortgage, 2=owned free and clear)
    - SPORDER: Person number (1 = householder)
    - PWGTP: Person weight
    - WGTP: Housing unit weight
    - PUMA: Public Use Microdata Area
    """
    # Check cache first
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    cache_file = os.path.join(OUTPUT_DIR, f'nyc_senior_homeowners_{year}.csv')

    if use_cache and os.path.exists(cache_file):
        print(f"Loading {year} data from cache...")
        df = pd.read_csv(cache_file)
        print(f"  Found {len(df)} 65+ homeowner households in NYC")
        print(f"  Weighted count: {df['WGTP'].sum():,.0f}")
        return df

    print(f"Fetching {year} ACS PUMS data from Census API...")

    # Use 1-year ACS for more recent years, 5-year for older
    if year >= 2019:
        dataset = f"{year}/acs/acs1/pums"
    else:
        dataset = f"{year}/acs/acs5/pums"

    url = f"https://api.census.gov/data/{dataset}"

    # First, get list of NYC PUMAs from the crosswalk
    # The PUMS API doesn't support county-level filtering directly,
    # but we can filter by place of work (POWPUMA) or use crosswalk

    # Get person-level data for all of NY state, then filter
    params = {
        'get': 'AGEP,HINCP,TEN,SPORDER,PWGTP,WGTP,PUMA',
        'for': 'state:36',  # New York State
        'key': CENSUS_API_KEY
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        df = pd.DataFrame(data[1:], columns=data[0])

        # Convert to numeric
        for col in ['AGEP', 'HINCP', 'TEN', 'SPORDER', 'PWGTP', 'WGTP']:
            df[col] = pd.to_numeric(df[col], errors='coerce')

        df['PUMA'] = df['PUMA'].astype(str).str.zfill(5)

        # Get NYC PUMAs from crosswalk file
        nyc_pumas = get_nyc_pumas_from_crosswalk(year)

        if nyc_pumas:
            df = df[df['PUMA'].isin(nyc_pumas)]
        else:
            # Fallback: NYC PUMAs are in the 03700-04200 range for all vintages
            # This is approximate but covers NYC across different PUMA vintages
            df['puma_int'] = df['PUMA'].astype(int)
            df = df[(df['puma_int'] >= 3700) & (df['puma_int'] <= 4200)]
            print("  (Using approximate PUMA range for NYC)")

        # Filter: householder (SPORDER=1), age 65+, owner-occupied (TEN in [1,2])
        df = df[(df['SPORDER'] == 1) &
                (df['AGEP'] >= 65) &
                (df['TEN'].isin([1, 2]))]

        print(f"  Found {len(df)} 65+ homeowner households in NYC")
        print(f"  Weighted count: {df['WGTP'].sum():,.0f}")

        # Save to cache
        df.to_csv(cache_file, index=False)
        print(f"  Cached to {cache_file}")

        return df

    except Exception as e:
        print(f"Error fetching PUMS data: {e}")
        return None


def get_nyc_pumas_from_crosswalk(year):
    """
    Get NYC PUMAs from Census crosswalk file.
    Downloads and caches the appropriate crosswalk.
    """
    # Determine which PUMA vintage to use
    if year <= 2011:
        vintage = '2000'
        crosswalk_url = 'https://www2.census.gov/geo/docs/reference/puma/2010_puma_equiv_txt.txt'
    elif year <= 2021:
        vintage = '2010'
        crosswalk_url = 'https://www2.census.gov/geo/docs/reference/puma/2010_puma_equiv_txt.txt'
    else:
        vintage = '2020'
        crosswalk_url = 'https://www2.census.gov/geo/docs/reference/puma/2020_Census_Tract_to_2020_PUMA.txt'

    cache_file = f'puma_crosswalk_{vintage}.csv'

    try:
        # Try to load cached crosswalk
        if os.path.exists(cache_file):
            xwalk = pd.read_csv(cache_file, dtype=str)
        else:
            # Download crosswalk
            print(f"  Downloading {vintage} PUMA crosswalk...")
            xwalk = pd.read_csv(crosswalk_url, dtype=str)
            xwalk.to_csv(cache_file, index=False)

        # Filter to NYC counties (36005, 36047, 36061, 36081, 36085)
        nyc_fips = ['36005', '36047', '36061', '36081', '36085']

        # Column names vary by file format
        if 'STATEFP' in xwalk.columns:
            xwalk['county_fips'] = xwalk['STATEFP'] + xwalk['COUNTYFP']
            puma_col = 'PUMA5CE' if 'PUMA5CE' in xwalk.columns else 'PUMA'
        else:
            # Try alternate format
            return None

        nyc_pumas = xwalk[xwalk['county_fips'].isin(nyc_fips)][puma_col].unique().tolist()

        print(f"  Found {len(nyc_pumas)} NYC PUMAs from crosswalk")
        return nyc_pumas

    except Exception as e:
        print(f"  Could not load crosswalk: {e}")
        return None


def get_acs_income_distribution(year):
    """
    Alternative: Use ACS summary tables for income distribution.
    Table B19037: Age of Householder by Household Income

    This is simpler but gives income brackets, not exact values.
    """
    print(f"Fetching {year} ACS income distribution for NYC...")

    # Use 5-year ACS for stability
    if year <= 2013:
        acs_year = 2010  # 2006-2010 5-year
        dataset = "2010/acs/acs5"
    else:
        acs_year = year
        dataset = f"{year}/acs/acs5"

    url = f"https://api.census.gov/data/{dataset}"

    # B19037: Age of Householder by Household Income
    # We need the 65+ rows (suffix _065 through _080 roughly)
    # Income brackets are: <10k, 10-15k, 15-20k, 20-25k, 25-30k, 30-35k, etc.

    # Get variable list - need to construct for 65+ householder income
    # B19037_062E through B19037_078E are for 65+ householder
    vars_65plus = [f'B19037_{str(i).zfill(3)}E' for i in range(62, 79)]

    params = {
        'get': ','.join(['NAME'] + vars_65plus),
        'for': 'county:061,005,047,081,085',  # NYC counties
        'in': 'state:36',
        'key': CENSUS_API_KEY
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        df = pd.DataFrame(data[1:], columns=data[0])

        # Convert to numeric and sum across NYC
        for col in vars_65plus:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        # Sum across all NYC counties
        totals = df[vars_65plus].sum()

        print(f"  Total 65+ households in NYC: {totals.sum():,.0f}")

        return totals

    except Exception as e:
        print(f"Error: {e}")
        # Try alternate table
        return get_acs_income_by_tenure_age(year)


def get_acs_income_by_tenure_age(year):
    """
    Use B25118: Tenure by Household Income
    Combined with age data to approximate 65+ homeowner income distribution.

    For a cleaner approach, use PUMS microdata.
    """
    print(f"Attempting alternate table for {year}...")
    return None


def compute_share_below_threshold(df, threshold=29000):
    """
    Compute weighted share of households below income threshold.
    """
    if df is None or len(df) == 0:
        return None

    below = df[df['HINCP'] < threshold]['WGTP'].sum()
    total = df['WGTP'].sum()

    share = below / total if total > 0 else 0

    print(f"  Share below ${threshold:,}: {share:.1%}")
    print(f"  Count below: {below:,.0f} / {total:,.0f}")

    return share


def create_income_histogram(df_early, df_late, year_early, year_late, threshold=29000):
    """
    Create overlaid histogram comparing income distributions with threshold line.
    Shades the area between distributions below the threshold to show coverage erosion.
    Uses non-uniform bins: 5k increments up to 60k, then coarser bins for upper tail.
    """
    if df_early is None or df_late is None:
        print("Missing data for histogram")
        return

    fig, ax = plt.subplots(figsize=(10, 6))

    # Non-uniform bins: 5k up to 60k, then coarser for upper tail
    # 0-5, 5-10, ..., 55-60, 60-80, 80-100, 100-140, 140+
    fine_bins = list(range(0, 65000, 5000))  # 0 to 60k in 5k increments
    coarse_bins = [80000, 100000, 140000, 500000]  # 60-80, 80-100, 100-140, 140+
    bins = np.array(fine_bins + coarse_bins)

    # Normalize weights
    weights_early = df_early['WGTP'] / df_early['WGTP'].sum()
    weights_late = df_late['WGTP'] / df_late['WGTP'].sum()

    # Clip incomes to max bin (everything above 140k goes in last bin)
    incomes_early = df_early['HINCP'].clip(lower=0)
    incomes_late = df_late['HINCP'].clip(lower=0)

    # Compute histogram values
    hist_early, bin_edges = np.histogram(incomes_early, bins=bins, weights=weights_early)
    hist_late, _ = np.histogram(incomes_late, bins=bins, weights=weights_late)

    # For plotting, use sequential x positions (equal width visually)
    n_bins = len(hist_early)
    x_positions = np.arange(n_bins)
    bar_width = 0.8

    # Create bin labels showing full range
    bin_labels = []
    for i in range(len(bins) - 1):
        left = bins[i] // 1000
        right = bins[i + 1] // 1000
        if right >= 500:
            bin_labels.append(f'>{left}')
        else:
            bin_labels.append(f'{left}-{right}')

    # Shade the difference between distributions below threshold
    for i in range(n_bins):
        bin_center_value = (bins[i] + bins[i + 1]) / 2
        if bin_center_value <= threshold:
            diff = hist_early[i] - hist_late[i]
            if diff > 0:
                # 2010 > 2023: lost eligibles (red)
                ax.bar(x_positions[i], diff, width=bar_width, bottom=hist_late[i],
                       color='lightcoral', alpha=0.6, edgecolor='none')
            elif diff < 0:
                # 2023 > 2010: gained eligibles (green)
                ax.bar(x_positions[i], -diff, width=bar_width, bottom=hist_early[i],
                       color='lightgreen', alpha=0.6, edgecolor='none')

    # Compute shares for legend
    share_early = compute_share_below_threshold(df_early, threshold)
    share_late = compute_share_below_threshold(df_late, threshold)

    # Plot bars: solid blue for early, hollow orange outline for late
    ax.bar(x_positions, hist_early, width=bar_width,
           alpha=0.6, color='steelblue', edgecolor='steelblue',
           label=f'{year_early}: {share_early:.0%} below limit')

    ax.bar(x_positions, hist_late, width=bar_width,
           fill=False, edgecolor='darkorange', linewidth=2,
           label=f'{year_late}: {share_late:.0%} below limit')

    # Add threshold line - find x position for $29k
    threshold_idx = np.searchsorted(bins[:-1], threshold, side='right') - 0.5
    ax.axvline(x=threshold_idx, color='darkred', linestyle='--', linewidth=2.5,
               label=f'SCHE income limit: ${threshold//1000}k')

    # Add median lines for each year
    def weighted_median(values, weights):
        sorted_idx = np.argsort(values)
        sorted_vals = values.iloc[sorted_idx]
        sorted_weights = weights.iloc[sorted_idx]
        cumsum = np.cumsum(sorted_weights)
        cutoff = cumsum.iloc[-1] / 2
        return sorted_vals.iloc[np.searchsorted(cumsum, cutoff)]

    median_early = weighted_median(df_early['HINCP'], df_early['WGTP'])
    median_late = weighted_median(df_late['HINCP'], df_late['WGTP'])

    # Find x positions for medians
    median_early_idx = np.searchsorted(bins[:-1], median_early, side='right') - 0.5
    median_late_idx = np.searchsorted(bins[:-1], median_late, side='right') - 0.5

    ax.axvline(x=median_early_idx, color='steelblue', linestyle=':', linewidth=2,
               label=f'{year_early} median: ${median_early/1000:.0f}k')
    ax.axvline(x=median_late_idx, color='darkorange', linestyle=':', linewidth=2,
               label=f'{year_late} median: ${median_late/1000:.0f}k')

    # Get weighted sample sizes for subtitle
    n_early = df_early['WGTP'].sum()
    n_late = df_late['WGTP'].sum()

    ax.set_xlabel('Household Income ($000s)', fontsize=11)
    ax.set_ylabel('Share of Households', fontsize=11)
    ax.set_title('NYC 65+ Homeowner Household Income Distribution\n'
                 f'SCHE income limit frozen at $29k (2009-2024). N = {n_early/1000:.0f}k ({year_early}), {n_late/1000:.0f}k ({year_late})',
                 fontsize=11)

    # Set x-axis ticks and labels
    ax.set_xticks(x_positions)
    ax.set_xticklabels(bin_labels, rotation=45, ha='right', fontsize=9)

    ax.legend(loc='upper right', fontsize=10)

    # Y-axis extends to max
    max_height = max(max(hist_early), max(hist_late))
    ax.set_ylim(0, max_height * 1.1)

    # Format y-axis as percentage
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f'{y:.0%}'))

    plt.tight_layout()

    # Save figure
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    filepath = os.path.join(OUTPUT_DIR, 'nyc_sche_coverage_erosion.pdf')
    plt.savefig(filepath, bbox_inches='tight', dpi=150)
    plt.savefig(filepath.replace('.pdf', '.png'), bbox_inches='tight', dpi=150)
    print(f"\nSaved: {filepath}")

    plt.close()

    return share_early, share_late


def main():
    """
    Main analysis: compare 2009 vs 2023 income distributions.
    """
    print("="*60)
    print("NYC SCHE Coverage Erosion Analysis")
    print("="*60)

    # Fetch PUMS data for early and late periods
    # 2009 1-year ACS or 2010 5-year ACS
    df_early = get_pums_data(2010)  # Use 2010 5-year (covers 2006-2010)

    # 2023 1-year ACS (most recent available)
    df_late = get_pums_data(2023)

    if df_early is not None and df_late is not None:
        # Compute shares
        print("\n" + "="*60)
        print("Results")
        print("="*60)

        share_early = compute_share_below_threshold(df_early, 29000)
        share_late = compute_share_below_threshold(df_late, 29000)

        if share_early and share_late:
            print(f"\nCoverage erosion: {share_early:.1%} -> {share_late:.1%}")
            print(f"Percentage point decline: {(share_early - share_late)*100:.1f} pp")

        # Create histogram
        create_income_histogram(df_early, df_late, 2010, 2023, threshold=29000)
    else:
        print("\nFailed to fetch PUMS data. Trying summary tables...")

        # Fallback to summary tables
        totals_2010 = get_acs_income_distribution(2010)
        totals_2023 = get_acs_income_distribution(2023)


if __name__ == "__main__":
    main()
