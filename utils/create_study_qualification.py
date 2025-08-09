# utils/create_study_qualification.py
import boto3

# Switch between sandbox and production
USE_SANDBOX = True  

ENDPOINT_URL = (
    "https://mturk-requester-sandbox.us-east-1.amazonaws.com"
    if USE_SANDBOX
    else "https://mturk-requester.us-east-1.amazonaws.com"
)

mturk = boto3.client("mturk", region_name="us-east-1", endpoint_url=ENDPOINT_URL)

resp = mturk.create_qualification_type(
    Name="StudyCompleted",
    Keywords="one-time,unique,block",
    Description="Blocks workers from taking the same study more than once",
    QualificationTypeStatus="Active"
)

qualification_id = resp["QualificationType"]["QualificationTypeId"]
print(f"✅ Created Qualification: {qualification_id}")
