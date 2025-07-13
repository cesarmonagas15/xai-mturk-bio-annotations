import boto3
import json
import xml.etree.ElementTree as ET
from pathlib import Path

# Load HIT ID
with open("../data/hit_metadata.json") as f:
    hit_data = json.load(f)
HIT_ID = hit_data["HITId"]

# Connect to MTurk Sandbox
mturk = boto3.client(
    'mturk',
    region_name='us-east-1',
    endpoint_url='https://mturk-requester-sandbox.us-east-1.amazonaws.com'
)

# Get assignments for the HIT
assignments = mturk.list_assignments_for_hit(
    HITId=HIT_ID,
    AssignmentStatuses=['Submitted', 'Approved'],
    MaxResults=10
)

print(f"Found {len(assignments['Assignments'])} assignments for HIT ID {HIT_ID}")

for assignment in assignments['Assignments']:
    worker_id = assignment['WorkerId']
    answer_xml = assignment['Answer']
    print(f"\nWorker: {worker_id}")

    # Parse the XML response
    root = ET.fromstring(answer_xml)
    for question in root.findall(".//QuestionFormAnswers/Answer"):
        qid = question.find("QuestionIdentifier").text
        ans = question.find("FreeText").text
        print(f"  {qid}: {ans}")
