"""
Analyze Florida NAL (Name-Address-Legal) property tax data.
Focus on senior exemptions (EXMPT_03, EXMPT_04).
"""

import pandas as pd
from pathlib import Path

# Data location
DATA_DIR = Path("/Users/jeffreyohl/Dropbox/PropertyTax/raw_data/florida_data/Assessor/2025")
NAL_FILE = DATA_DIR / "NAL23F202501.csv"  # Miami-Dade, 2025 Final

# Columns to load (subset to reduce memory)
COLS_TO_LOAD = [
    "CO_NO",
    "PARCEL_ID",
    "ASMNT_YR",
    "DOR_UC",  # DOR use code
    "JV",  # Just value (market value)
    "AV_SD",  # Assessed value - school district
    "TV_SD",  # Taxable value - school district
    "JV_HMSTD",  # Just value - homestead
    "AV_HMSTD",  # Assessed value - homestead
    "LND_VAL",
    "OWN_NAME",
    "OWN_CITY",
    "OWN_STATE",
    "PHY_CITY",
    "PHY_ZIPCD",
    # Exemption fields
    "EXMPT_01",  # Homestead $25k
    "EXMPT_02",  # Additional homestead $25k
    "EXMPT_03",  # County senior 65+ low-income
    "EXMPT_04",  # Municipal senior 65+ low-income
    "EXMPT_05",  # Disabled veteran
    "EXMPT_06",  # Disabled veteran wheelchair
    "EXMPT_07",  # Child care facility
    "EXMPT_08",  # Totally disabled
]


def load_nal(filepath: Path, cols: list = None) -> pd.DataFrame:
    """Load NAL file with optional column subset."""
    print(f"Loading {filepath.name}...")
    df = pd.read_csv(filepath, usecols=cols, low_memory=False)
    print(f"  Loaded {len(df):,} parcels")
    return df


def summarize_exemptions(df: pd.DataFrame) -> None:
    """Print summary of exemption usage."""
    print("\n" + "=" * 60)
    print("EXEMPTION SUMMARY")
    print("=" * 60)

    exemption_cols = [c for c in df.columns if c.startswith("EXMPT_")]

    for col in exemption_cols:
        # Count non-zero/non-null values
        has_exemption = (df[col].notna()) & (df[col] != 0)
        n_claiming = has_exemption.sum()
        pct_claiming = 100 * n_claiming / len(df)

        if n_claiming > 0:
            values = df.loc[has_exemption, col]
            print(f"\n{col}:")
            print(f"  Parcels claiming: {n_claiming:,} ({pct_claiming:.2f}%)")
            print(f"  Mean value: ${values.mean():,.0f}")
            print(f"  Median value: ${values.median():,.0f}")
            print(f"  Max value: ${values.max():,.0f}")
            print(f"  Min value: ${values.min():,.0f}")


def analyze_senior_exemptions(df: pd.DataFrame) -> None:
    """Deep dive on senior exemptions (EXMPT_03, EXMPT_04)."""
    print("\n" + "=" * 60)
    print("SENIOR EXEMPTION ANALYSIS (EXMPT_03 = County, EXMPT_04 = Municipal)")
    print("=" * 60)

    # EXMPT_03: County senior exemption
    has_03 = (df["EXMPT_03"].notna()) & (df["EXMPT_03"] > 0)
    senior_03 = df[has_03].copy()

    print(f"\nEXMPT_03 (County senior 65+ low-income):")
    print(f"  Parcels: {len(senior_03):,}")

    if len(senior_03) > 0:
        print(f"\n  Value distribution:")
        print(senior_03["EXMPT_03"].describe())

        print(f"\n  Top exemption amounts (potential policy caps):")
        print(senior_03["EXMPT_03"].value_counts().head(10))

    # EXMPT_04: Municipal senior exemption
    has_04 = (df["EXMPT_04"].notna()) & (df["EXMPT_04"] > 0)
    senior_04 = df[has_04].copy()

    print(f"\n\nEXMPT_04 (Municipal senior 65+ low-income):")
    print(f"  Parcels: {len(senior_04):,}")

    if len(senior_04) > 0:
        print(f"\n  Value distribution:")
        print(senior_04["EXMPT_04"].describe())

        print(f"\n  Top exemption amounts (potential policy caps):")
        print(senior_04["EXMPT_04"].value_counts().head(10))

    # Both exemptions
    has_both = has_03 & has_04
    print(f"\n\nParcels with BOTH county and municipal senior exemptions: {has_both.sum():,}")


def homestead_vs_senior(df: pd.DataFrame) -> None:
    """Compare homestead exemption to senior exemption usage."""
    print("\n" + "=" * 60)
    print("HOMESTEAD VS SENIOR EXEMPTION OVERLAP")
    print("=" * 60)

    has_homestead = (df["EXMPT_01"].notna()) & (df["EXMPT_01"] > 0)
    has_senior_03 = (df["EXMPT_03"].notna()) & (df["EXMPT_03"] > 0)
    has_senior_04 = (df["EXMPT_04"].notna()) & (df["EXMPT_04"] > 0)
    has_any_senior = has_senior_03 | has_senior_04

    print(f"\nHomestead (EXMPT_01): {has_homestead.sum():,} parcels")
    print(f"Any senior exemption: {has_any_senior.sum():,} parcels")
    print(f"Senior exemption without homestead: {(has_any_senior & ~has_homestead).sum():,}")
    print(f"Senior exemption with homestead: {(has_any_senior & has_homestead).sum():,}")

    # Senior exemption implies homestead?
    if has_any_senior.sum() > 0:
        pct_senior_with_homestead = 100 * (has_any_senior & has_homestead).sum() / has_any_senior.sum()
        print(f"\n% of senior exemption holders who also have homestead: {pct_senior_with_homestead:.1f}%")


if __name__ == "__main__":
    df = load_nal(NAL_FILE, COLS_TO_LOAD)

    summarize_exemptions(df)
    analyze_senior_exemptions(df)
    homestead_vs_senior(df)
