# aws/create_hits_from_all_batches.py

import random
from pathlib import Path
from create_hit_from_batch import create_hit_from_batch

# === CONFIG ===
batches_dir = Path("../data/batches/")
template_path = Path("../templates/hit_template.html")
meta_dir = Path("../data/hit_metadata/")
reward = "0.50"  # default reward
frame_height = 600

# Optional: seed for reproducibility
random.seed(42)

# === Get all batch files and separate by type ===
all_batch_files = sorted(batches_dir.glob("*.json"))
plain_batches = [f for f in all_batch_files if "plain" in f.name]
explanation_batches = [f for f in all_batch_files if "explanation" in f.name]

print(f"🔍 Found {len(plain_batches)} plain batches and {len(explanation_batches)} explanation batches")

# === Create HITs by randomly selecting batch types ===
num_hits_to_create = 4  # or however many HITs you want

for i in range(num_hits_to_create):
    # Randomly choose between plain and explanation
    batch_type = random.choice(["plain", "explanation"])
    
    if batch_type == "plain":
        available_batches = plain_batches
        condition = "baseline"
    else:
        available_batches = explanation_batches
        condition = "explanation"
    
    # Randomly select a batch from the chosen type
    batch_file = random.choice(available_batches)
    
    print(f"🚀 Launching HIT {i+1}: {batch_file.name} with condition: {condition}")
    try:
        result = create_hit_from_batch(
            batch_path=batch_file,
            template_path=template_path,
            meta_dir=meta_dir,
            reward=reward,
            frame_height=frame_height,
            condition=condition
        )
        if result is None:
            print(f"⏭️ Skipped {batch_file.name} (max usage reached)")
    except Exception as e:
        print(f"❌ Failed to create HIT for {batch_file.name}: {e}")
