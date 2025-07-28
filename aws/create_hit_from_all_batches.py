# aws/create_hits_from_all_batches.py

from pathlib import Path
from mturk_utils import create_hit_from_batch

# === CONFIG ===
batches_dir = Path("../data/batches/")
template_path = Path("../templates/hit_template.html")
meta_dir = Path("../data/hit_metadata/")
reward = "0.50"  # default reward
frame_height = 600

# === Iterate through all batch JSON files ===
batch_files = sorted(batches_dir.glob("*.json"))

if not batch_files:
    print("⚠️ No batch files found in:", batches_dir.resolve())
else:
    print(f"🔍 Found {len(batch_files)} batch files to publish...\n")

for batch_file in batch_files:
    print(f"🚀 Launching HIT for: {batch_file.name}")
    try:
        create_hit_from_batch(
            batch_path=batch_file,
            template_path=template_path,
            output_meta_dir=meta_dir,
            reward=reward,
            frame_height=frame_height
        )
    except Exception as e:
        print(f"❌ Failed to create HIT for {batch_file.name}: {e}")
