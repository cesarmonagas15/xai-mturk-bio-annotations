import csv
from pathlib import Path

# Load bios from CSV
with open("data/sample_bio.csv", newline='') as csvfile:
    reader = csv.DictReader(csvfile)
    bios = list(reader)

# Create HTML blocks for each bio
bio_blocks = []
for i, row in enumerate(bios):
    bio_html = f"""
    <div class="step" id="step{i + 1}" style="display: none;">
        <p><img src="{row['image_exp_bio']}" alt="Explanation Image" width="400"/></p>
        <p><strong>Predicted Occupation:</strong> {row['predicted_occ']}</p>
        <p><label>What is your prediction?</label><br/>
        <input type="radio" name="response_{i}" value="Physician"/> Physician<br/>
        <input type="radio" name="response_{i}" value="Nurse"/> Nurse</p>
    </div>
    """
    bio_blocks.append(bio_html)

# Join all bio steps into a single HTML string
all_bio_html = "\n".join(bio_blocks)

# Load the base template
base_template_path = Path("templates/hit_template.html")
with open(base_template_path, "r") as f:
    base_template = f.read()

# Inject the bio blocks
final_html = base_template.replace("<!--INSERT_BIO_BLOCKS_HERE-->", all_bio_html)

# Save the completed HTML file
output_path = Path("templates/hit_template.html")
with open(output_path, "w") as f:
    f.write(final_html)

print(f"✅ HIT template generated at {output_path.resolve()}")
