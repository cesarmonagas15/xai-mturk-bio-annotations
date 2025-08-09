import boto3
import json
import uuid
from string import Template
from pathlib import Path
from datetime import datetime

def create_hit_from_batch(batch_path, template_path, meta_dir, reward, frame_height, condition, max_usage_per_batch=3):
    """Create a MTurk HIT from a batch of bios using a template."""
    meta_dir.mkdir(parents=True, exist_ok=True)

    # ==== Check if batch has reached maximum usage ====
    batch_stem = batch_path.stem
    usage_tracker_file = meta_dir / "batch_usage_tracker.json"
    
    if usage_tracker_file.exists():
        with open(usage_tracker_file, 'r') as f:
            usage_counts = json.load(f)
    else:
        usage_counts = {}
    
    current_usage = usage_counts.get(batch_stem, 0)
    if current_usage >= max_usage_per_batch:
        print(f"⚠️ Skipping {batch_path.name} - already used {current_usage} times (max: {max_usage_per_batch})")
        return None

    # ==== Load batch bios ====
    with open(batch_path) as f:
        batch_bios = json.load(f)

    num_bios = len(batch_bios)

    # ==== Build condition-specific intro ====
    if "explanation" in condition.lower():
        intro_text = f"""
        <div class="step">
            <h2>Instructions</h2>
            <p>You will now be shown {num_bios} short biographies and for each asked to predict whether the person whose biography you are reading is a physician or a nurse.</p>
            <p>To assist your decision, for each biography you will be shown the predicted occupation from an Aritificial Intelligence (AI).</p>
            <p>Note that the AI's predictions need not always be correct.</p>
            <p>In addition to the predicted occupation, the AI also provides a highlighting of words that most influenced its prediction: The color indicates the occupation a word is predictive of (blue for physician, orange for nurse), and the color intensity shows the importance of a word in the AI's prediction.</p>
            <div class="navigation">
                <button type="button" onclick="nextStep()">Start Task</button>
            </div>
        </div>
        """
    else:
        intro_text = f"""
        <div class="step">
            <h2>Instructions</h2>
            <p>You will now be shown {num_bios} short biographies and for each asked to predict whether the person whose biography you are reading is a physician or a nurse.</p>
            <p>To assist your decision, for each biography you will be shown the predicted occupation from an Artificial Intelligence (AI). Note that the AI's predictions need not always be correct.</p></br>
            <p>Your task starts on the next page.</p>
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
            <p><img src="{item['image_url']}" alt="Bio Image" width="700"/></p>
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

    # ==== Thank you + transition ====
    bio_blocks.append(""" 
    <div class="step">
        <h2>Thank You!</h2>
        <p>Thank you for completing the task!</p>
        <p>On the following pages, we kindly ask you to answer some additional questions.</p>
        <div class="navigation">
            <button type="button" onclick="nextStep()">Continue</button>
        </div>
    </div>
    """)

    # ==== Perceptions Block (only for experimental condition) ====
    if "explanation" in condition.lower():
        perceptions_block = """
        <div class="step">
            <p>The following three questions refer to the procedures the AI uses to predict a person’s occupation. Please rate your agreement with the following statements.</p>

            <p class="question-label">1. The AI's procedures are free of bias.</p>
            <label class="perception-group"><input type="radio" name="bias_free" value="Fully disagree" required> Fully disagree</label>
            <label class="perception-group"><input type="radio" name="bias_free" value="Somewhat disagree"> Somewhat disagree</label>
            <label class="perception-group"><input type="radio" name="bias_free" value="Neither agree nor disagree"> Neither agree nor disagree</label>
            <label class="perception-group"><input type="radio" name="bias_free" value="Somewhat agree"> Somewhat agree</label>
            <label class="perception-group"><input type="radio" name="bias_free" value="Fully agree"> Fully agree</label>

            <p class="question-label">2. The AI's procedures uphold ethical and moral standards.</p>
            <label class="perception-group"><input type="radio" name="ethical" value="Fully disagree" required> Fully disagree</label>
            <label class="perception-group"><input type="radio" name="ethical" value="Somewhat disagree"> Somewhat disagree</label>
            <label class="perception-group"><input type="radio" name="ethical" value="Neither agree nor disagree"> Neither agree nor disagree</label>
            <label class="perception-group"><input type="radio" name="ethical" value="Somewhat agree"> Somewhat agree</label>
            <label class="perception-group"><input type="radio" name="ethical" value="Fully agree"> Fully agree</label>

            <p class="question-label">3. It is fair that the AI considers the highlighted words for predicting a person's occupation.</p>
            <label class="perception-group"><input type="radio" name="fairness" value="Fully disagree" required> Fully disagree</label>
            <label class="perception-group"><input type="radio" name="fairness" value="Somewhat disagree"> Somewhat disagree</label>
            <label class="perception-group"><input type="radio" name="fairness" value="Neither agree nor disagree"> Neither agree nor disagree</label>
            <label class="perception-group"><input type="radio" name="fairness" value="Somewhat agree"> Somewhat agree</label>
            <label class="perception-group"><input type="radio" name="fairness" value="Fully agree"> Fully agree</label>

            <div class="navigation">
                <button type="button" onclick="nextStep()">Next</button>
            </div>
        </div>
        """
        bio_blocks.append(perceptions_block)


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

    # ==== Random suffix to break HIT group hashing ====
    random_suffix = uuid.uuid4().hex[:6]

    # ==== Create HIT ====
    mturk = boto3.client(
        'mturk',
        region_name='us-east-1',
        endpoint_url='https://mturk-requester-sandbox.us-east-1.amazonaws.com'
    )
    response = mturk.create_hit(
        Title=f'Decide Occupation from Bio Images [{random_suffix}]',
        Description=f'Review bios and answer questions. Ref: {random_suffix}',
        Keywords='bio, annotation, healthcare',
        Reward=reward,
        MaxAssignments=3,
        LifetimeInSeconds=604800,
        AssignmentDurationInSeconds=7200,
        AutoApprovalDelayInSeconds=86400,
        Question=question_xml
        QualificationRequirements=[
        # {
        #     'QualificationTypeId': '000000000000000000L0',  # Approval rate
        #     'Comparator': 'GreaterThanOrEqualTo',
        #     'IntegerValues': [95],
        #     'ActionsGuarded': 'DiscoverPreviewAndAccept'
        # },
        # {
        #     'QualificationTypeId': '00000000000000000040',  # HITs approved
        #     'Comparator': 'GreaterThanOrEqualTo',
        #     'IntegerValues': [500],
        #     'ActionsGuarded': 'DiscoverPreviewAndAccept'
        # },
        # {
        #     'QualificationTypeId': '00000000000000000071',  # Locale
        #     'Comparator': 'EqualTo',
        #     'LocaleValues': [{'Country': 'US'}],
        #     'ActionsGuarded': 'DiscoverPreviewAndAccept'
        # },
        {
              'QualificationTypeId': QUALIFICATION_TYPE_ID,
              'Comparator': 'DoesNotExist'
        }
        ]
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
        "bios": batch_bios,
        "random_suffix": random_suffix
    }

    # Save metadata with usage count
    usage_count = current_usage + 1
    meta_file = meta_dir / f"{batch_stem}_hit_metadata_{usage_count}.json"
    meta_file.write_text(json.dumps(metadata, indent=2))

    # Update usage tracker
    usage_counts[batch_stem] = usage_count
    with open(usage_tracker_file, 'w') as f:
        json.dump(usage_counts, f, indent=2)

    print("✅ HIT created:")
    print(f"🔗 Preview: https://workersandbox.mturk.com/mturk/preview?groupId={group_id}")
    print(f"📁 Metadata: {meta_file.resolve()}")
    print(f"📊 Usage count for {batch_path.name}: {usage_count}/{max_usage_per_batch}")

    return metadata

# Optional: standalone run
if __name__ == "__main__":
    batch_path = Path("../data/batches/batch_1.json")
    template_path = Path("../templates/hit_template.html")
    meta_dir = Path("../data/hit_metadata/")
    reward = "0.50"
    frame_height = 600
    condition = "explanation"
    create_hit_from_batch(batch_path, template_path, meta_dir, reward, frame_height, condition)
