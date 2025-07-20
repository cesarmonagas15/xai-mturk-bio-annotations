import csv
import random
import os
from pathlib import Path
import json

# === CONFIG ===
INPUT_CSV = Path("../data/bio_image_links_s3.csv")  # Path to CSV with bio_id, variant, s3_url
OUTPUT_DIR = Path("../data/batches/")                # Directory where batches will be stored
NUM_BATCHES = 2                                      # Total number of batches to create (change as needed)
BIOS_PER_BATCH = 20                                  # Number of bios per batch
RANDOM_SEED = 42                                     # For reproducibility

# === SETUP ===
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

with open(INPUT_CSV, newline='') as csvfile:
    reader = csv.DictReader(csvfile)
    all_entries = list(reader)

# Group by bio_id
bios_by_id = {}
for row in all_entries:
    bio_id = row['bio_id']
    variant = row['variant']  # 'plain' or 'explanation'
    url = row['s3_url']
    if bio_id not in bios_by_id:
        bios_by_id[bio_id] = {}
    bios_by_id[bio_id][variant] = url

# Get only bios that have both variants
valid_bios = [bio_id for bio_id, variants in bios_by_id.items() if 'plain' in variants and 'explanation' in variants]
print(f"✅ Found {len(valid_bios)} valid bios with both variants")

random.seed(RANDOM_SEED)
random.shuffle(valid_bios)

bios_needed = NUM_BATCHES * BIOS_PER_BATCH
if len(valid_bios) < bios_needed:
    raise ValueError(f"Not enough bios to create {NUM_BATCHES} batches of {BIOS_PER_BATCH}. Needed: {bios_needed}, Found: {len(valid_bios)}")

# Create batches
for batch_index in range(NUM_BATCHES):
    start = batch_index * BIOS_PER_BATCH
    end = start + BIOS_PER_BATCH
    batch_bios = valid_bios[start:end]

    # Randomly assign variant (condition) for each bio in the batch
    batch_entries = []
    for bio_id in batch_bios:
        condition = random.choice(['plain', 'explanation'])
        entry = {
            "bio_id": bio_id,
            "condition": condition,
            "image_url": bios_by_id[bio_id][condition]
        }
        batch_entries.append(entry)

    # Save batch to JSON
    out_path = OUTPUT_DIR / f"batch_{batch_index+1}.json"
    with open(out_path, "w") as f:
        json.dump(batch_entries, f, indent=2)
    print(f"✅ Wrote batch {batch_index+1} to {out_path.resolve()}")
