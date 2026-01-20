"""
Download Florida millage rate PDFs (Table 1 - Comparison of Levies) for all 67 counties.

URL pattern: https://floridarevenue.com/property/dataportal/Documents/PTO%20Data%20Portal/County%20Municipal%20Reports/Table%201-Comparison%20of%20Levies/{YY}table1/{County} Table 1.pdf

Years available: 2008-2024 (08table1 through 24table1)

Usage:
    python download_millage_pdfs.py --year 2024 --output /path/to/output
    python download_millage_pdfs.py --all-years --output /path/to/output
"""

import argparse
import requests
from pathlib import Path
from urllib.parse import quote
import time

# Florida counties - names as they appear in millage PDF URLs
# Note: "Dade" in NAL files is "Miami-Dade" in millage PDFs
FLORIDA_COUNTIES = [
    "Alachua", "Baker", "Bay", "Bradford", "Brevard", "Broward",
    "Calhoun", "Charlotte", "Citrus", "Clay", "Collier", "Columbia",
    "Miami-Dade",  # NOT "Dade"
    "DeSoto", "Dixie", "Duval", "Escambia", "Flagler", "Franklin",
    "Gadsden", "Gilchrist", "Glades", "Gulf", "Hamilton", "Hardee",
    "Hendry", "Hernando", "Highlands", "Hillsborough", "Holmes",
    "Indian River", "Jackson", "Jefferson", "Lafayette", "Lake",
    "Lee", "Leon", "Levy", "Liberty", "Madison", "Manatee", "Marion",
    "Martin", "Monroe", "Nassau", "Okaloosa", "Okeechobee", "Orange",
    "Osceola", "Palm Beach", "Pasco", "Pinellas", "Polk", "Putnam",
    "Santa Rosa", "Sarasota", "Seminole", "St. Johns", "St. Lucie",
    "Sumter", "Suwannee", "Taylor", "Union", "Volusia", "Wakulla",
    "Walton", "Washington",
]

BASE_URL = "https://floridarevenue.com/property/dataportal/Documents/PTO%20Data%20Portal/County%20Municipal%20Reports/Table%201-Comparison%20of%20Levies"


def download_county_millage(county: str, year: int, output_dir: Path) -> bool:
    """Download millage PDF for a single county/year. Returns True if successful."""
    yy = str(year)[-2:]  # e.g., 2024 -> "24"
    filename = f"{county} Table 1.pdf"
    url = f"{BASE_URL}/{yy}table1/{quote(filename)}"

    # Output filename includes year for clarity
    output_filename = f"{county}_Table1_{year}.pdf"
    output_path = output_dir / output_filename

    if output_path.exists():
        print(f"  Skipping {county} {year} (already exists)")
        return True

    try:
        response = requests.get(url, timeout=60)
        response.raise_for_status()

        with open(output_path, 'wb') as f:
            f.write(response.content)

        size_kb = len(response.content) / 1024
        print(f"  {county} {year}: OK ({size_kb:.0f} KB)")
        return True

    except requests.exceptions.HTTPError as e:
        print(f"  {county} {year}: FAILED ({e.response.status_code})")
        return False
    except Exception as e:
        print(f"  {county} {year}: FAILED ({e})")
        return False


def main():
    parser = argparse.ArgumentParser(description="Download Florida millage rate PDFs")
    parser.add_argument("--year", type=int, help="Single year to download (e.g., 2024)")
    parser.add_argument("--all-years", action="store_true", help="Download all years 2008-2024")
    parser.add_argument("--output", type=str, required=True, help="Output directory")
    parser.add_argument("--county", type=str, help="Download single county (optional)")
    parser.add_argument("--delay", type=float, default=0.3, help="Delay between downloads in seconds")
    args = parser.parse_args()

    if not args.year and not args.all_years:
        parser.error("Must specify either --year or --all-years")

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.all_years:
        years = list(range(2008, 2025))  # 2008-2024
    else:
        years = [args.year]

    if args.county:
        if args.county not in FLORIDA_COUNTIES:
            print(f"Unknown county: {args.county}")
            print(f"Valid counties: {', '.join(sorted(FLORIDA_COUNTIES))}")
            return
        counties = [args.county]
    else:
        counties = FLORIDA_COUNTIES

    print(f"Downloading millage PDFs")
    print(f"Years: {min(years)}-{max(years)}")
    print(f"Counties: {len(counties)}")
    print(f"Output: {output_dir}")
    print()

    success = 0
    failed = []

    for year in years:
        print(f"\n=== {year} ===")
        for county in sorted(counties):
            if download_county_millage(county, year, output_dir):
                success += 1
            else:
                failed.append((county, year))

            if args.delay > 0:
                time.sleep(args.delay)

    total = len(years) * len(counties)
    print(f"\n\nDownloaded: {success}/{total}")
    if failed:
        print(f"Failed ({len(failed)}):")
        for county, year in failed[:20]:  # Show first 20
            print(f"  {county} {year}")
        if len(failed) > 20:
            print(f"  ... and {len(failed) - 20} more")


if __name__ == "__main__":
    main()
