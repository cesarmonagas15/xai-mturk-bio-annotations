import boto3
import csv
import io

BONUS_AMOUNT = "0.10"  # $0.10 per correct answer
BONUS_REASON = "Bonus for correctly identifying the occupation."
MTURK_SANDBOX_URL = 'https://mturk-requester-sandbox.us-east-1.amazonaws.com'

def lambda_handler(event, context):
    s3 = boto3.client("s3")
    mturk = boto3.client("mturk", endpoint_url=MTURK_SANDBOX_URL)

    bucket = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']

    response = s3.get_object(Bucket=bucket, Key=key)
    content = response['Body'].read().decode('utf-8')
    reader = csv.DictReader(io.StringIO(content))

    bonuses = {}

    for row in reader:
        if row.get("correct", "").lower() == "true":
            worker = row["worker_id"]
            assignment = row["assignment_id"]
            bonuses.setdefault((worker, assignment), 0)
            bonuses[(worker, assignment)] += 1

    for (worker_id, assignment_id), num_correct in bonuses.items():
        total_bonus = float(BONUS_AMOUNT) * num_correct
        try:
            mturk.send_bonus(
                WorkerId=worker_id,
                BonusAmount=str(round(total_bonus, 2)),
                AssignmentId=assignment_id,
                Reason=BONUS_REASON
            )
            print(f"✅ Sent ${total_bonus} to {worker_id} for assignment {assignment_id}")
        except Exception as e:
            print(f"❌ Failed to send bonus to {worker_id}: {e}")
