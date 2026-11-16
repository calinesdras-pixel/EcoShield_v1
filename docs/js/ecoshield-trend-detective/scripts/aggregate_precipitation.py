import csv
import calendar
import math
from pathlib import Path
from collections import defaultdict

PROJECT_ROOT = Path(__file__).resolve().parent.parent

INPUT_FILE = PROJECT_ROOT / "data/processed/precipitation_gabon.csv"
OUTPUT_FILE = PROJECT_ROOT / "data/processed/precipitation_nationale_mensuelle.csv"

observations = defaultdict(list)

# Lecture des observations
with open(INPUT_FILE, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)

    for row in reader:
        value = float(row["precipitation"])
        latitude = float(row["latitude"])

        if not math.isfinite(value) or value < 0:
            continue

        weight = math.cos(math.radians(latitude))

        observations[row["date"]].append({
            "value": value,
            "weight": weight
        })

# Agrégation mensuelle
results = []

for date in sorted(observations):

    values = observations[date]

    total_weight = sum(item["weight"] for item in values)

    weighted_mean = sum(
        item["value"] * item["weight"]
        for item in values
    ) / total_weight

    year = int(date[:4])
    month = int(date[4:6])

    days = calendar.monthrange(year, month)[1]

    estimated_total = weighted_mean * days

    results.append({
        "date": f"{year}-{month:02d}",
        "mean_mm_per_day": round(weighted_mean, 4),
        "estimated_monthly_mm": round(estimated_total, 2),
        "points_used": len(values)
    })

# Export CSV
with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:

    fieldnames = [
        "date",
        "mean_mm_per_day",
        "estimated_monthly_mm",
        "points_used"
    ]

    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(results)

print("\n========== AGRÉGATION NATIONALE ==========")
print("Nombre de mois :", len(results))
print("Premier mois :", results[0]["date"] if results else "Aucun")
print("Dernier mois :", results[-1]["date"] if results else "Aucun")
print("Points utilisés par mois :",
      sorted(set(r["points_used"] for r in results)))

print("\nPremières observations :")

for row in results[:5]:
    print(row)

print("\nFichier généré :", OUTPUT_FILE)
print("========== TERMINÉ ==========")