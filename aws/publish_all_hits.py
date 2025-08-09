# # publish_all_hits.py

# from pathlib import Path
# from create_hit_from_batch import create_hit_from_batch

# BATCH_DIR = Path("../data/batches/")
# META_DIR = Path("../data/hit_metadata/")
# TEMPLATE_PATH = Path("../templates/hit_template.html")

# # Find all batch files
# batch_files = sorted(BATCH_DIR.glob("batch_*.json"))
# print(f"📦 Found {len(batch_files)} batch files.")

# for batch_path in batch_files:
#     metadata_file = META_DIR / f"{batch_path.stem}_hit_metadata.json"
#     if metadata_file.exists():
#         print(f"⏭️  Skipping {batch_path.name} (already published)")
#         continue

#     try:
#         create_hit_from_batch(
#             batch_path=batch_path,
#             template_path=TEMPLATE_PATH,
#             meta_dir=META_DIR
#         )
#     except Exception as e:
#         print(f"❌ Failed to create HIT for {batch_path.name}: {e}")
