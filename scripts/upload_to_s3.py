import os
import boto3
import pandas as pd

# Settings
BUCKET_NAME = "mturk-bio-images-cesar"
LOCAL_IMAGE_DIR = "../data/bios"
OUTPUT_CSV_PATH = "../data/bio_image_links_s3.csv"

# Initialize S3 client
s3 = boto3.client("s3")

def upload_images_and_get_links():
    records = []

    for filename in os.listdir(LOCAL_IMAGE_DIR):
        if filename.endswith(".png"):
            full_path = os.path.join(LOCAL_IMAGE_DIR, filename)

            # Upload to S3
            s3.upload_file(
                Filename=full_path,
                Bucket=BUCKET_NAME,
                Key=filename,
                ExtraArgs={'ContentType': 'image/png'}
            )

            # Parse metadata
            bio_id, variant = filename.replace(".png", "").split("_")

            # Construct public URL
            url = f"https://{BUCKET_NAME}.s3.amazonaws.com/{filename}"

            records.append({
                "bio_id": int(bio_id),
                "variant": variant,
                "s3_url": url
            })

    return records

if __name__ == "__main__":
    print("Uploading images to S3...")
    records = upload_images_and_get_links()
    df = pd.DataFrame(records)
    df.sort_values(["bio_id", "variant"], inplace=True)
    os.makedirs(os.path.dirname(OUTPUT_CSV_PATH), exist_ok=True)
    df.to_csv(OUTPUT_CSV_PATH, index=False)
    print(f"✅ Done! CSV saved to {OUTPUT_CSV_PATH} with {len(df)} image links.")
