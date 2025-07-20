import boto3
import json
from string import Template
from pathlib import Path

# ==== CONFIG ====
batch_path = Path("../data/batches/batch_1.json") # Only batch1 for now
template_path = Path("../templates/hit_template.html")
output_meta_path = Path("../data/hit_metadata.json")
frame_height = 600

# ==== Load batch ====
with open(batch_path) as f:
    batch_bios = json.load(f)

# ==== Generate HTML for each bio block ====
bio_blocks = []
for i, item in enumerate(batch_bios, start=1):
    bio_html = f"""
    <div class="step">
        <h3>Bio {i} of {len(batch_bios)}</h3>
        <p><img src="{item['image_url']}" alt="Bio Image" width="400"/></p>
        <p>
            <label>What is your prediction?</label><br/>
            <input type="radio" name="occupation_{i}" value="Physician" required> Physician<br/>
            <input type="radio" name="occupation_{i}" value="Nurse" required> Nurse
        </p>
        <div class="navigation">
            <button type="button" onclick="prevStep()">Back</button>
            <button type="button" onclick="nextStep()">Next</button>
        </div>
    </div>
    """
    bio_blocks.append(bio_html)

bio_blocks_combined = "\n".join(bio_blocks)

# ==== Inject into HTML template ====
with open(template_path) as f:
    template = Template(f.read())

question_html = template.substitute(bio_blocks=bio_blocks_combined)

# ==== Wrap in XML ====
question_xml = f"""
<HTMLQuestion xmlns="http://mechanicalturk.amazonaws.com/AWSMechanicalTurkDataSchemas/2011-11-11/HTMLQuestion.xsd">
  <HTMLContent><![CDATA[
    {question_html}
  ]]></HTMLContent>
  <FrameHeight>{frame_height}</FrameHeight>
</HTMLQuestion>
"""

# ==== Create HIT ====
mturk = boto3.client(
    'mturk',
    region_name='us-east-1',
    endpoint_url='https://mturk-requester-sandbox.us-east-1.amazonaws.com'
)

response = mturk.create_hit(
    Title='Decide Occupation from Bio Images',
    Description='Read short bios and decide the occupation of each person.',
    Keywords='bio, annotation, healthcare',
    Reward='0.50',
    MaxAssignments=3,
    LifetimeInSeconds=3600,
    AssignmentDurationInSeconds=600,
    AutoApprovalDelayInSeconds=86400,
    Question=question_xml
)

# ==== Save HIT metadata ====
hit_id = response['HIT']['HITId']
group_id = response['HIT']['HITGroupId']

output_meta_path.write_text(json.dumps({"HITId": hit_id, "HITGroupId": group_id}, indent=2))

print("✅ HIT created:")
print(f"Preview link: https://workersandbox.mturk.com/mturk/preview?groupId={group_id}")
