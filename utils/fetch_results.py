import boto3
import csv
import json
import xml.etree.ElementTree as ET
from pathlib import Path
import pandas as pd

# === CONFIG ===
HIT_METADATA_DIR = Path("../data/hit_metadata")
MASTER_CSV_PATH = Path("../data/master.csv")  # Ground truth for bio_id
BIO_CSV_OUT = Path("../data/worker_bio_level_responses.csv")
ASSIGNMENT_CSV_OUT = Path("../data/worker_assignment_level_meta.csv")
S3_BUCKET_NAME = "mturk-bio-results-cesar"

# === CONNECT TO MTURK ===
mturk = boto3.client(
    'mturk',
    region_name='us-east-1',
    endpoint_url='https://mturk-requester-sandbox.us-east-1.amazonaws.com'
)

# === CONNECT TO S3 ===
s3 = boto3.client('s3')

# === LOAD MASTER FILE ===
master_df = pd.read_csv(MASTER_CSV_PATH)
master_df['id'] = master_df['id'].astype(str)

# === FIND HIT METADATA FILES ===
metadata_files = list(HIT_METADATA_DIR.glob("*_hit_metadata_*.json"))
print(f"\n📂 Found {len(metadata_files)} metadata files")

bio_level_records = []
assignment_level_records = []

for meta_path in metadata_files:
    with open(meta_path) as f:
        hit_meta = json.load(f)

    bios = hit_meta["bios"]
    condition = bios[0].get("condition", "unknown")  # assume same condition across all bios
    HIT_ID = hit_meta["HITId"]

    assignments = mturk.list_assignments_for_hit(
        HITId=HIT_ID,
        AssignmentStatuses=['Submitted', 'Approved'],
        MaxResults=100
    )['Assignments']

    print(f"\n🔍 {meta_path.name} → {len(assignments)} assignments")

    for assignment in assignments:
        assignment_id = assignment['AssignmentId']
        worker_id = assignment['WorkerId']
        answer_xml = assignment['Answer']
        accept_time = assignment['AcceptTime']
        submit_time = assignment['SubmitTime']

        root = ET.fromstring(answer_xml)
        ns = {'ns': 'http://mechanicalturk.amazonaws.com/AWSMechanicalTurkDataSchemas/2005-10-01/QuestionFormAnswers.xsd'}

        demo_data = {"assignment_id": assignment_id, "worker_id": worker_id, "condition": condition}
        perception_data = {}

        for answer in root.findall(".//ns:Answer", ns):
            qid = answer.find("ns:QuestionIdentifier", ns).text
            response = answer.find("ns:FreeText", ns).text

            # === Demographics or Perception ===
            if qid in ["age", "gender", "race", "education", "ai_experience"]:
                demo_data[qid] = response
                continue
            elif qid in ["bias_free", "ethical", "fairness"]:
                perception_data[qid] = response
                continue

            # === Occupation Responses ===
            if qid.startswith("occupation_"):
                try:
                    index = int(qid.replace("occupation_", "")) - 1
                    bio_entry = bios[index]
                    bio_id = str(bio_entry['bio_id'])
                    master_row = master_df[master_df['id'] == bio_id]
                    if master_row.empty:
                        continue
                    true_label = master_row.iloc[0]['true_occupation']
                    correct = response.strip().lower() == true_label.strip().lower()

                    bio_level_records.append({
                        "assignment_id": assignment_id,
                        "worker_id": worker_id,
                        "bio_id": bio_id,
                        "response": response,
                        "true_occupation": true_label,
                        "correct": correct,
                        "accept_time": accept_time,
                        "submit_time": submit_time
                    })
                except Exception as e:
                    print(f"⚠️ Failed to parse {qid}: {e}")
                    continue

        # === Add demographics + perceptions
        demo_data.update(perception_data)
        assignment_level_records.append(demo_data)

# === SAVE TO CSVs ===
pd.DataFrame(bio_level_records).to_csv(BIO_CSV_OUT, index=False)
print(f"\n📄 Saved {len(bio_level_records)} responses to {BIO_CSV_OUT}")

pd.DataFrame(assignment_level_records).to_csv(ASSIGNMENT_CSV_OUT, index=False)
print(f"📄 Saved {len(assignment_level_records)} assignment-level records to {ASSIGNMENT_CSV_OUT}")

# === UPLOAD TO S3 ===
with open(BIO_CSV_OUT, "rb") as f:
    s3.upload_fileobj(f, S3_BUCKET_NAME, BIO_CSV_OUT.name)
    print(f"☁️ Uploaded to s3://{S3_BUCKET_NAME}/{BIO_CSV_OUT.name}")

with open(ASSIGNMENT_CSV_OUT, "rb") as f:
    s3.upload_fileobj(f, S3_BUCKET_NAME, ASSIGNMENT_CSV_OUT.name)
    print(f"☁️ Uploaded to s3://{S3_BUCKET_NAME}/{ASSIGNMENT_CSV_OUT.name}")
