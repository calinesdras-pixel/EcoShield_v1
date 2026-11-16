import csv
from pathlib import Path
from collections import defaultdict

PROJECT_ROOT = Path(__file__).resolve().parent.parent

INPUT_FILE = (
    PROJECT_ROOT
    / "data/processed/precipitation_nationale_mensuelle.csv"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "data/processed/precipitation_nationale_annuelle.csv"
)

annual_data = defaultdict(list)

# Lire les données mensuelles
with open(INPUT_FILE, "r", encoding="utf-8") as f:

    reader = csv.DictReader(f)

    for row in reader:

        year = int(row["date"][:4])
        month = int(row["date"][5:7])

        monthly_rainfall = float(row["estimated_monthly_mm"])
        daily_mean = float(row["mean_mm_per_day"])

        annual_data[year].append({
            "month": month,
            "rainfall": monthly_rainfall,
            "daily_mean": daily_mean
        })

results = []

# Calculer les cumuls annuels
for year in sorted(annual_data):

    months = annual_data[year]

    total_rainfall = sum(
        item["rainfall"] for item in months
    )

    total_days = sum(
        __import__("calendar").monthrange(year, item["month"])[1]
        for item in months
    )

    annual_daily_mean = total_rainfall / total_days

    results.append({
        "year": year,
        "annual_precipitation_mm": round(total_rainfall, 2),
        "mean_daily_precipitation_mm": round(annual_daily_mean, 4),
        "months_available": len(months),
        "complete_year": len(months) == 12
    })

# Exporter les résultats
with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:

    fieldnames = [
        "year",
        "annual_precipitation_mm",
        "mean_daily_precipitation_mm",
        "months_available",
        "complete_year"
    ]

    writer = csv.DictWriter(f, fieldnames=fieldnames)

    writer.writeheader()
    writer.writerows(results)

# Bilan
print("\n========== AGRÉGATION ANNUELLE ==========")

print("Nombre d'années :", len(results))

if results:

    print("Première année :", results[0]["year"])
    print("Dernière année :", results[-1]["year"])

    incomplete = [
        row for row in results
        if not row["complete_year"]
    ]

    print("Années complètes :", len(results) - len(incomplete))
    print("Années incomplètes :", len(incomplete))

    print("\n========== PRÉCIPITATIONS ANNUELLES ==========")

    for row in results:
        print(row)

    if not incomplete:
        wettest = max(
            results,
            key=lambda x: x["annual_precipitation_mm"]
        )

        driest = min(
            results,
            key=lambda x: x["annual_precipitation_mm"]
        )

        print("\nAnnée la plus pluvieuse :", wettest)
        print("Année la moins pluvieuse :", driest)

print("\nFichier généré :", OUTPUT_FILE)
print("========== TERMINÉ ==========")