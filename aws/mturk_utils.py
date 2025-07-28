# mturk_utils.py

import boto3
import json
from string import Template
from pathlib import Path
from datetime import datetime

def create_hit_from_batch(
    batch_path: Path,
    template_path: Path,
    output_meta_dir: Path,
    reward: str = "0.50",
    frame_height: int = 600,
    title: str = None,
    description: str = None,
    max_assignments: int = 3
) -> dict:
    """
    Creates an MTurk HIT from a given batch file and HTML template.

    Args:
        batch_path (Path): Path to the JSON batch file (list of bios).
        template_path (Path): Path to the HIT HTML template file.
        output_meta_dir (Path): Directory to store metadata.
        reward (str): Payment amount in USD per assignment (default $0.50).
        frame_height (int): Frame height for the HIT UI.
        title (str): Optional title override.
        description (str): Optional description override.
        max_assignments (int): Number of annotators per HIT (default 3).

    Returns:
        dict: HIT metadata including HITId, HITGroupId, batch info, etc.
    """
    output_meta_dir.mkdir(parents=True, exist_ok=True)

    condition = batch_path.stem.replace("batch_", "")
    with open(batch_path) as f:
        batch_bios = json.load(f)

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
                <button type="button" onclick="nextStep()">Next</button>
            </div>
        </div>
        """
        bio_blocks.append(bio_html)

    with open(template_path) as f:
        template = Template(f.read())

    question_html = template.substitute(bio_blocks="\n".join(bio_blocks))

    question_xml = f"""
    <HTMLQuestion xmlns="http://mechanicalturk.amazonaws.com/AWSMechanicalTurkDataSchemas/2011-11-11/HTMLQuestion.xsd">
      <HTMLContent><![CDATA[
        {question_html}
      ]]></HTMLContent>
      <FrameHeight>{frame_height}</FrameHeight>
    </HTMLQuestion>
    """

    mturk = boto3.client(
        'mturk',
        region_name='us-east-1',
        endpoint_url='https://mturk-requester-sandbox.us-east-1.amazonaws.com'
    )

    response = mturk.create_hit(
        Title=title or f'Decide Occupation from Bio Images - Batch {batch_path.stem}',
        Description=description or f'Annotation task for {condition} condition, batch {batch_path.stem}',
        Keywords='bio, annotation, healthcare',
        Reward=reward,
        MaxAssignments=max_assignments,
        LifetimeInSeconds=3600,
        AssignmentDurationInSeconds=600,
        AutoApprovalDelayInSeconds=86400,
        Question=question_xml
    )

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

    meta_file = output_meta_dir / f"{batch_path.stem}_hit_metadata.json"
    meta_file.write_text(json.dumps(metadata, indent=2))

    print("✅ HIT created:")
    print(f"🔗 Preview link: https://workersandbox.mturk.com/mturk/preview?groupId={group_id}")
    print(f"📁 Metadata saved to: {meta_file.resolve()}")

    return metadata
