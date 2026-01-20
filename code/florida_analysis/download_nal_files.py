"""
Download Florida NAL (Name-Address-Legal) files for all 67 counties.

URL pattern: https://floridarevenue.com/property/dataportal/Documents/PTO%20Data%20Portal/Tax%20Roll%20Data%20Files/NAL/{year}F/{County} {code} Final NAL {year}.zip

Usage:
    python download_nal_files.py --year 2025 --output /path/to/output
"""

import argparse
import requests
from pathlib import Path
from urllib.parse import quote
import time

# Florida counties with their DOR codes
# Source: https://floridarevenue.com/property/Pages/DataPortal.aspx
FLORIDA_COUNTIES = {
    "Alachua": 11,
    "Baker": 12,
    "Bay": 13,
    "Bradford": 14,
    "Brevard": 15,
    "Broward": 16,
    "Calhoun": 17,
    "Charlotte": 18,
    "Citrus": 19,
    "Clay": 20,
    "Collier": 21,
    "Columbia": 22,
    "Dade": 23,  # Miami-Dade
    "DeSoto": 24,
    "Dixie": 25,
    "Duval": 26,
    "Escambia": 27,
    "Flagler": 28,
    "Franklin": 29,
    "Gadsden": 30,
    "Gilchrist": 31,
    "Glades": 32,
    "Gulf": 33,
    "Hamilton": 34,
    "Hardee": 35,
    "Hendry": 36,
    "Hernando": 37,
    "Highlands": 38,
    "Hillsborough": 39,
    "Holmes": 40,
    "Indian River": 41,
    "Jackson": 42,
    "Jefferson": 43,
    "Lafayette": 44,
    "Lake": 45,
    "Lee": 46,
    "Leon": 47,
    "Levy": 48,
    "Liberty": 49,
    "Madison": 50,
    "Manatee": 51,
    "Marion": 52,
    "Martin": 53,
    "Monroe": 54,
    "Nassau": 55,
    "Okaloosa": 56,
    "Okeechobee": 57,
    "Orange": 58,
    "Osceola": 59,
    "Palm Beach": 60,
    "Pasco": 61,
    "Pinellas": 62,
    "Polk": 63,
    "Putnam": 64,
    "Santa Rosa": 65,
    "Sarasota": 66,
    "Seminole": 67,
    "St. Johns": 68,
    "St. Lucie": 69,
    "Sumter": 70,
    "Suwannee": 71,
    "Taylor": 72,
    "Union": 73,
    "Volusia": 74,
    "Wakulla": 75,
    "Walton": 76,
    "Washington": 77,
}

BASE_URL = "https://floridarevenue.com/property/dataportal/Documents/PTO%20Data%20Portal/Tax%20Roll%20Data%20Files/NAL"


def download_county(county: str, code: int, year: int, output_dir: Path) -> bool:
    """Download NAL file for a single county. Returns True if successful."""
    filename = f"{county} {code} Final NAL {year}.zip"
    url = f"{BASE_URL}/{year}F/{quote(filename)}"
    output_path = output_dir / filename

    if output_path.exists():
        print(f"  Skipping {county} (already exists)")
        return True

    print(f"  Downloading {county}...", end=" ", flush=True)

    try:
        response = requests.get(url, stream=True, timeout=300)
        response.raise_for_status()

        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        size_mb = output_path.stat().st_size / (1024 * 1024)
        print(f"OK ({size_mb:.1f} MB)")
        return True

    except requests.exceptions.HTTPError as e:
        print(f"FAILED ({e.response.status_code})")
        return False
    except Exception as e:
        print(f"FAILED ({e})")
        return False


def main():
    parser = argparse.ArgumentParser(description="Download Florida NAL files")
    parser.add_argument("--year", type=int, default=2025, help="Tax year (default: 2025)")
    parser.add_argument("--output", type=str, required=True, help="Output directory")
    parser.add_argument("--county", type=str, help="Download single county (optional)")
    parser.add_argument("--delay", type=float, default=1.0, help="Delay between downloads in seconds")
    args = parser.parse_args()

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Downloading NAL files for {args.year}")
    print(f"Output directory: {output_dir}")
    print()

    if args.county:
        # Single county
        if args.county not in FLORIDA_COUNTIES:
            print(f"Unknown county: {args.county}")
            print(f"Valid counties: {', '.join(sorted(FLORIDA_COUNTIES.keys()))}")
            return
        counties = {args.county: FLORIDA_COUNTIES[args.county]}
    else:
        counties = FLORIDA_COUNTIES

    success = 0
    failed = []

    for county, code in sorted(counties.items(), key=lambda x: x[1]):
        if download_county(county, code, args.year, output_dir):
            success += 1
        else:
            failed.append(county)

        if args.delay > 0 and county != list(counties.keys())[-1]:
            time.sleep(args.delay)

    print()
    print(f"Downloaded: {success}/{len(counties)}")
    if failed:
        print(f"Failed: {', '.join(failed)}")


if __name__ == "__main__":
    main()
