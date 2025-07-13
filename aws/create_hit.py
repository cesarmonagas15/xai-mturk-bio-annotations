import boto3
import csv
from string import Template
import json
from pathlib import Path

# Load HTML template
with open("../templates/hit_template.html", "r") as file:
    html_template = Template(file.read())

# Load bio from CSV (for now we just grab one row)
with open("../data/sample_bio.csv", newline='') as csvfile:
    reader = csv.DictReader(csvfile)
    bios = list(reader)
    first_bio = bios[0]  # just using the first for prototype

# Fill in HTML template
question_html = html_template.substitute(
    bio=first_bio["bio"],
    predicted_occ=first_bio["predicted_occ"],
    image_url=first_bio["image_exp_bio"]
)

# Wrap with XML envelope (HTMLQuestion format)
question_xml = f"""
<HTMLQuestion xmlns="http://mechanicalturk.amazonaws.com/AWSMechanicalTurkDataSchemas/2011-11-11/HTMLQuestion.xsd">
  <HTMLContent><![CDATA[
    {question_html}
  ]]></HTMLContent>
  <FrameHeight>600</FrameHeight>
</HTMLQuestion>
"""

# Connect to MTurk Sandbox
mturk = boto3.client(
    'mturk',
    region_name='us-east-1',
    endpoint_url='https://mturk-requester-sandbox.us-east-1.amazonaws.com'
)

# Create HIT
response = mturk.create_hit(
    Title='Decide Occupation from Bio',
    Description='Read a short bio and decide the person’s occupation.',
    Keywords='bio, occupation, annotation',
    Reward='0.02',
    MaxAssignments=1,
    LifetimeInSeconds=3600,
    AssignmentDurationInSeconds=60,
    AutoApprovalDelayInSeconds=86400,
    Question=question_xml
)

print("HIT created. You can preview it here:")
print("https://workersandbox.mturk.com/mturk/preview?groupId=" + response['HIT']['HITGroupId'])

# Save HIT ID to a local file
output_path = Path("../data/hit_metadata.json")
with open(output_path, "w") as f:
    json.dump({
        "HITId": response['HIT']['HITId']
    }, f)

print(f"HIT ID stored in: {output_path.resolve()}")
