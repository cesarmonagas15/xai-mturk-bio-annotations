import boto3

# MTurk Sandbox client
mturk = boto3.client(
    'mturk',
    region_name='us-east-1',
    endpoint_url='https://mturk-requester-sandbox.us-east-1.amazonaws.com'
)

# Get list of HITs
hits = mturk.list_hits()['HITs']
print(f"🔍 Found {len(hits)} HITs")

for hit in hits:
    hit_id = hit['HITId']
    try:
        # Expire the HIT by setting its expiration to now
        mturk.update_expiration_for_hit(
            HITId=hit_id,
            ExpireAt=0  # 0 means immediately expire
        )
        print(f"✅ Expired HIT: {hit_id}")
    except Exception as e:
        print(f"❌ Failed to expire HIT {hit_id}: {e}")
