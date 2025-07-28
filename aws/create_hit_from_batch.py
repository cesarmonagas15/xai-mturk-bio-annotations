import boto3
import json
from string import Template
from pathlib import Path
from datetime import datetime

def create_hit_from_batch(batch_path, template_path, meta_dir):
    """Create a MTurk HIT from a batch of bios using a template."""
    frame_height = 600
    meta_dir.mkdir(parents=True, exist_ok=True)
    
    # ==== Extract condition ====
    condition = batch_path.stem.replace("batch_", "")
    
    # ==== Load batch bios ====
    with open(batch_path) as f:
        batch_bios = json.load(f)

    num_bios = len(batch_bios)

    # ==== Build condition-specific intro ====
    if "explanation" in condition.lower():
        intro_text = f"""
        <div class="step">
            <h2>Instructions</h2>
            <p>You will now be shown {num_bios} short biographies and for each asked to predict whether the person is a physician or a nurse.</p>
            <p>To assist your decision, you will see the predicted occupation from an AI.</p>
            <p>In addition, the AI highlights words that influenced its decision. Blue words suggest "physician", orange words suggest "nurse", and darker colors mean stronger influence. See the example below.</p>
            <div class="navigation">
                <button type="button" onclick="nextStep()">Start Task</button>
            </div>
        </div>
        """
    else:
        intro_text = f"""
        <div class="step">
            <h2>Instructions</h2>
            <p>You will now be shown {num_bios} short biographies and for each asked to predict whether the person is a physician or a nurse.</p>
            <p>To assist your decision, you will see the predicted occupation from an AI. Note: The AI’s prediction is not always correct.</p>
            <div class="navigation">
                <button type="button" onclick="nextStep()">Start Task</button>
            </div>
        </div>
        """

    # ==== Build bio blocks ====
    bio_blocks = [intro_text]
    for i, item in enumerate(batch_bios, start=1):
        block = f"""
        <div class="step">
            <h3>Bio {i} of {num_bios}</h3>
            <p><img src="{item['image_url']}" alt="Bio Image" width="400"/></p>
            <p>
                <label>What is your prediction?</label><br/>
                <input type="radio" name="occupation_{i}" value="Physician" required> Physician<br/>
                <input type="radio" name="occupation_{i}" value="Nurse" required> Nurse
            </p>
            <div class="navigation">
                <button type="button" onclick="nextStep()">Next</button>
            </div>
        </div>
        """
        bio_blocks.append(block)

    # ==== Thank you +  transition to demographics ====
    bio_blocks.append(""" 
    <div class="step">
        <h2>Thank You!</h2>
        <p>Thank you for completing the task!</p>
        <p>On the following pages, we kindly ask you to answer some additional demographic questions.</p>
        <div class="navigation">
            <button type="button" onclick="nextStep()">Continue</button>
        </div>
    </div>
    """)

    bio_blocks_combined = "\n".join(bio_blocks)

    # ==== Load template and substitute ====
    with open(template_path) as f:
        template = Template(f.read())

    question_html = template.safe_substitute(bio_blocks=bio_blocks_combined, condition=condition)


    # ==== Wrap in XML ====
    question_xml = f"""
    <HTMLQuestion xmlns="http://mechanicalturk.amazonaws.com/AWSMechanicalTurkDataSchemas/2011-11-11/HTMLQuestion.xsd">
      <HTMLContent><![CDATA[
        {question_html}
      ]]></HTMLContent>
      <FrameHeight>{frame_height}</FrameHeight>
    </HTMLQuestion>
    """

    # ==== Worker Qualification Requirements ====
    # qualification_requirements = [
    #     {
    #         'QualificationTypeId': '000000000000000000L0',  # HIT approval rate
    #         'Comparator': 'GreaterThanOrEqualTo',
    #         'IntegerValues': [95],
    #         'ActionsGuarded': 'DiscoverPreviewAndAccept'
    #     },
    #     {
    #         'QualificationTypeId': '00000000000000000040',  # Approved HITs
    #         'Comparator': 'GreaterThanOrEqualTo',
    #         'IntegerValues': [100],
    #         'ActionsGuarded': 'DiscoverPreviewAndAccept'
    #     },
    #     {
    #         'QualificationTypeId': '00000000000000007100',  # Locale requirement
    #         'Comparator': 'EqualTo',
    #         'LocaleValues': [
    #             {
    #                 'Country': 'US'
    #             }
    #         ],
    #         'ActionsGuarded': 'DiscoverPreviewAndAccept'
    #     }
    # ]



    # ==== Create HIT ====
    mturk = boto3.client(
        'mturk',
        region_name='us-east-1',
        endpoint_url='https://mturk-requester-sandbox.us-east-1.amazonaws.com'
    )
    response = mturk.create_hit(
        Title=f'Decide Occupation from Bio Images - Batch {batch_path.stem}',
        Description=f'Annotation task for {condition} condition, batch {batch_path.stem}',
        Keywords='bio, annotation, healthcare',
        Reward='0.50',
        MaxAssignments=3,
        LifetimeInSeconds=3600,
        AssignmentDurationInSeconds=600,
        AutoApprovalDelayInSeconds=86400,
        Question=question_xml,
        # QualificationRequirements=qualification_requirements
    )

    # ==== Save metadata ====
    hit_id = response['HIT']['HITId']
    group_id = response['HIT']['HITGroupId']
    timestamp = datetime.utcnow().isoformat() + "Z"

    metadata = {
        "HITId": hit_id,
        "HITGroupId": group_id,
        "created_at": timestamp,
        "batch_file": batch_path.name,
        "condition": condition,
        "bios": batch_bios
    }

    meta_file = meta_dir / f"{batch_path.stem}_hit_metadata.json"
    meta_file.write_text(json.dumps(metadata, indent=2))

    print("✅ HIT created:")
    print(f"🔗 Preview: https://workersandbox.mturk.com/mturk/preview?groupId={group_id}")
    print(f"📁 Metadata: {meta_file.resolve()}")

    return metadata

# Run manually if needed
if __name__ == "__main__":
    batch_path = Path("../data/batches/batch_explanation_1.json")
    template_path = Path("../templates/hit_template.html")
    meta_dir = Path("../data/hit_metadata/")
    create_hit_from_batch(batch_path, template_path, meta_dir)
