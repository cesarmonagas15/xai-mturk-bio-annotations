import csv
import random
import os
from pathlib import Path
import json

# === CONFIG ===
INPUT_CSV = Path("../data/bio_image_links_s3.csv")  # bio_id, variant, s3_url
OUTPUT_DIR = Path("../data/batches/")
BATCHES_PER_CONDITION = 5        
BIOS_PER_BATCH = 20
MAX_USAGE_PER_BIO = 3
RANDOM_SEED = 42

# === SETUP ===
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
random.seed(RANDOM_SEED)

# Load all entries
with open(INPUT_CSV, newline='') as csvfile:
    reader = csv.DictReader(csvfile)
    entries = list(reader)

# Group URLs by condition and bio_id
images_by_condition = {'plain': {}, 'explanation': {}}
for row in entries:
    condition = row['variant']  # 'plain' or 'explanation'
    bio_id = row['bio_id']
    url = row['s3_url']
    images_by_condition[condition][bio_id] = url

# Initialize counters
usage_counts = {
    'plain': {bio_id: 0 for bio_id in images_by_condition['plain']},
    'explanation': {bio_id: 0 for bio_id in images_by_condition['explanation']}
}

# === CREATE BATCHES PER CONDITION ===
for condition in ['plain', 'explanation']:
    print(f"\nCreating batches for condition: {condition}")
    available_bios = list(images_by_condition[condition].keys())
    random.shuffle(available_bios)
    
    for batch_index in range(BATCHES_PER_CONDITION):
        # Sample 20 bios that haven't been used 3 times yet
        eligible_bios = [bio_id for bio_id in available_bios if usage_counts[condition][bio_id] < MAX_USAGE_PER_BIO]

        if len(eligible_bios) < BIOS_PER_BATCH:
            raise ValueError(f"Not enough eligible bios to create batch {batch_index+1} for condition '{condition}'")

        selected_bios = random.sample(eligible_bios, BIOS_PER_BATCH)

        # Update usage counts and remove bios if maxed out
        for bio_id in selected_bios:
            usage_counts[condition][bio_id] += 1
            if usage_counts[condition][bio_id] >= MAX_USAGE_PER_BIO:
                available_bios.remove(bio_id)

        # Create batch entries
        batch_entries = [{
            "bio_id": bio_id,
            "condition": condition,
            "image_url": images_by_condition[condition][bio_id]
        } for bio_id in selected_bios]

        # Save to file
        batch_filename = f"batch_{condition}_{batch_index+1}.json"
        batch_path = OUTPUT_DIR / batch_filename
        with open(batch_path, "w") as f:
            json.dump(batch_entries, f, indent=2)

        print(f"✅ Wrote {batch_filename} with {len(batch_entries)} bios")

