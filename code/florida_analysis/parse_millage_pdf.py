"""
Parse Florida millage rate PDFs (Table 1 - Comparison of Levies).

Returns structured DataFrames of county and municipal millage rates.
"""

import re
import pdfplumber
import pandas as pd
from pathlib import Path
from dataclasses import dataclass


@dataclass
class MillageRates:
    """Container for parsed millage data."""
    county_name: str
    fiscal_year: str  # e.g., "2024-25"
    county_rates: pd.DataFrame  # BCC, Fire, Library, UMSA, etc.
    municipal_rates: pd.DataFrame  # City name, millage rate


def parse_millage_pdf(pdf_path: Path) -> MillageRates:
    """
    Extract millage rates from a Florida Table 1 PDF.

    Args:
        pdf_path: Path to the PDF file

    Returns:
        MillageRates object with county and municipal rates
    """
    with pdfplumber.open(pdf_path) as pdf:
        # These PDFs are typically single-page
        text = "\n".join(page.extract_text() or "" for page in pdf.pages)

    # Extract county name
    county_match = re.search(r"County:\s*([A-Z\-]+)", text)
    county_name = county_match.group(1) if county_match else "UNKNOWN"

    # Extract fiscal year (the "As Adopted" year)
    fy_match = re.search(r"(\d{4}-\d{2})\s*$", text.split("\n")[3] if len(text.split("\n")) > 3 else "")
    if not fy_match:
        fy_match = re.search(r"and\s+(\d{4}-\d{2})", text)
    fiscal_year = fy_match.group(1) if fy_match else "UNKNOWN"

    # Parse county-level rates (BCC, Fire, Library, UMSA)
    county_rates = _extract_county_rates(text)

    # Parse municipal rates
    municipal_rates = _extract_municipal_rates(text)

    return MillageRates(
        county_name=county_name,
        fiscal_year=fiscal_year,
        county_rates=county_rates,
        municipal_rates=municipal_rates,
    )


def _extract_county_rates(text: str) -> pd.DataFrame:
    """Extract county-level millage rates (BCC, Fire, Library, UMSA)."""
    rates = []

    # Pattern for county rate lines: name followed by millage rate
    # e.g., "Miami-Dade BCC 4.5740 $ 1,933,324,462 ..."
    # We want the "As Adopted" rate which is the 5th numeric field

    patterns = [
        (r"BCC\s+([\d.]+)\s+\$", "BCC"),
        (r"Fire/Rescue\s+([\d.]+)\s+\$", "Fire/Rescue"),
        (r"Library\s+([\d.]+)\s+\$", "Library"),
        (r"Mun Srvc Area-Umsa\s+([\d.]+)\s+\$", "UMSA"),
    ]

    for pattern, name in patterns:
        match = re.search(pattern, text)
        if match:
            # The first rate in the line is 2023-24, we want 2024-25 (adopted)
            # Need to find all rates on that line
            line_match = re.search(rf"{name}.*?(\d+\.\d+).*?(\d+\.\d+).*?(\d+\.\d+)", text, re.IGNORECASE)
            if line_match:
                # Third rate is the adopted rate for current year
                adopted_rate = float(line_match.group(3))
                rates.append({"authority": name, "millage_rate": adopted_rate})

    return pd.DataFrame(rates)


def _extract_municipal_rates(text: str) -> pd.DataFrame:
    """Extract municipal millage rates."""
    rates = []

    # Pattern: "City of X" or "Town of X" or "X Village" followed by rate
    # The adopted rate is after the third $ sign on each line

    lines = text.split("\n")

    for line in lines:
        # Skip county-level lines and headers
        if any(x in line for x in ["BCC", "Fire/Rescue", "Library", "UMSA", "TOTAL", "Taxing Authority", "Rolled-Back"]):
            continue

        # Match municipality patterns (include hyphens in names like Opa-Locka)
        muni_match = re.match(
            r"(City of [\w\s\-]+|Town of [\w\s\-]+|[\w\s\-]+ Village|Village of [\w\s\-]+)\s+([\d.]+)\s+\$",
            line.strip()
        )

        if muni_match:
            muni_name = muni_match.group(1).strip()
            # Extract all rates from the line to get the adopted rate
            all_rates = re.findall(r"(\d+\.\d{4})", line)
            if len(all_rates) >= 3:
                # Third rate is adopted
                adopted_rate = float(all_rates[2])
            else:
                # Fallback to first rate
                adopted_rate = float(muni_match.group(2))

            rates.append({
                "municipality": muni_name,
                "millage_rate": adopted_rate,
            })

    return pd.DataFrame(rates)


def normalize_municipality_name(name: str) -> str:
    """
    Normalize municipality name for matching between NAL and millage PDF.

    PDF uses: "City of Miami", "Town of Cutler Bay", "Village of Pinecrest"
    NAL uses: "Miami", "Cutler Bay", "Pinecrest"
    """
    # Remove prefixes
    name = re.sub(r"^(City of |Town of |Village of )", "", name, flags=re.IGNORECASE)
    # Normalize case and whitespace
    name = name.strip().upper()
    return name


def build_municipality_crosswalk(rates: MillageRates) -> dict[str, float]:
    """
    Build a lookup from normalized municipality name to millage rate.

    Returns:
        Dict mapping uppercase municipality name -> millage rate
    """
    # Known variations between NAL PHY_CITY and millage PDF names
    ALIASES = {
        "MIAMI SHORES VILLAGE": ["MIAMI SHORES"],
    }

    crosswalk = {}
    for _, row in rates.municipal_rates.iterrows():
        normalized = normalize_municipality_name(row["municipality"])
        crosswalk[normalized] = row["millage_rate"]

        # Add aliases
        if normalized in ALIASES:
            for alias in ALIASES[normalized]:
                crosswalk[alias] = row["millage_rate"]

    return crosswalk


def get_total_county_millage(rates: MillageRates, incorporated: bool = True) -> float:
    """
    Get total county millage rate.

    Args:
        rates: Parsed millage rates
        incorporated: If True, exclude UMSA (for parcels in cities)
                     If False, include UMSA (for unincorporated parcels)

    Returns:
        Total county millage rate (per $1000)
    """
    df = rates.county_rates
    if incorporated:
        df = df[df["authority"] != "UMSA"]
    return df["millage_rate"].sum()


def compute_exemption_savings(
    nal_df: pd.DataFrame,
    rates: MillageRates,
) -> pd.DataFrame:
    """
    Compute dollar savings from senior exemptions for each parcel.

    Args:
        nal_df: NAL DataFrame with PHY_CITY, EXMPT_03, EXMPT_04 columns
        rates: Parsed millage rates

    Returns:
        DataFrame with added columns:
        - county_millage: applicable county millage rate
        - municipal_millage: applicable municipal millage rate
        - county_savings: EXMPT_03 * county_millage / 1000
        - municipal_savings: EXMPT_04 * municipal_millage / 1000
        - total_savings: county_savings + municipal_savings
    """
    df = nal_df.copy()

    # Get county millage rates
    county_incorporated = get_total_county_millage(rates, incorporated=True)
    county_unincorporated = get_total_county_millage(rates, incorporated=False)

    # Build municipal crosswalk
    muni_crosswalk = build_municipality_crosswalk(rates)

    # Normalize PHY_CITY for matching
    df["_phy_city_norm"] = df["PHY_CITY"].fillna("").str.strip().str.upper()

    # Determine if incorporated
    df["is_unincorporated"] = df["_phy_city_norm"].str.contains("UNINCORPORATED", na=False)

    # Assign county millage
    df["county_millage"] = df["is_unincorporated"].map(
        {True: county_unincorporated, False: county_incorporated}
    )

    # Assign municipal millage (0 for unincorporated)
    df["municipal_millage"] = df["_phy_city_norm"].map(muni_crosswalk).fillna(0.0)

    # Compute savings (millage is per $1000)
    df["county_savings"] = df["EXMPT_03"].fillna(0) * df["county_millage"] / 1000
    df["municipal_savings"] = df["EXMPT_04"].fillna(0) * df["municipal_millage"] / 1000
    df["total_savings"] = df["county_savings"] + df["municipal_savings"]

    # Clean up temp columns
    df = df.drop(columns=["_phy_city_norm"])

    return df


if __name__ == "__main__":
    # Test with Miami-Dade PDF
    pdf_path = Path("/Users/jeffreyohl/Dropbox/PropertyTax/raw_data/florida_data/MillageRates/2024/Miami-Dade Table 1 (1).pdf")

    rates = parse_millage_pdf(pdf_path)

    print(f"County: {rates.county_name}")
    print(f"Fiscal Year: {rates.fiscal_year}")

    print("\n--- County Rates ---")
    print(rates.county_rates)
    print(f"\nTotal (incorporated): {get_total_county_millage(rates, incorporated=True):.4f}")
    print(f"Total (unincorporated): {get_total_county_millage(rates, incorporated=False):.4f}")

    print("\n--- Municipal Rates ---")
    print(rates.municipal_rates.to_string())

    # Test crosswalk
    print("\n--- Crosswalk Test ---")
    crosswalk = build_municipality_crosswalk(rates)
    test_cities = ["MIAMI", "OPA-LOCKA", "AVENTURA", "CORAL GABLES", "PINECREST"]
    for city in test_cities:
        rate = crosswalk.get(city, "NOT FOUND")
        print(f"  {city}: {rate}")

    # Test savings computation on NAL data
    print("\n--- Exemption Savings Test ---")
    nal_path = Path("/Users/jeffreyohl/Dropbox/PropertyTax/raw_data/florida_data/Assessor/2025/NAL23F202501.csv")
    cols = ["PHY_CITY", "EXMPT_03", "EXMPT_04"]
    nal_df = pd.read_csv(nal_path, usecols=cols, low_memory=False)

    df = compute_exemption_savings(nal_df, rates)

    # Filter to parcels with senior exemptions
    has_senior = (df["EXMPT_03"] > 0) | (df["EXMPT_04"] > 0)
    senior_df = df[has_senior]

    print(f"\nParcels with senior exemptions: {len(senior_df):,}")
    print(f"\nSavings summary:")
    print(senior_df[["county_savings", "municipal_savings", "total_savings"]].describe())

    print("\n--- Savings by Municipality (Top 15) ---")
    by_city = senior_df.groupby("PHY_CITY").agg({
        "total_savings": ["count", "mean", "min", "max"],
        "municipal_millage": "first",
    }).round(2)
    by_city.columns = ["count", "mean_savings", "min_savings", "max_savings", "muni_millage"]
    by_city = by_city.sort_values("count", ascending=False)
    print(by_city.head(15).to_string())
