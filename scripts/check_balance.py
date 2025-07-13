# scripts/check_balance.py
import boto3

mturk = boto3.client(
    'mturk',
    region_name='us-east-1',
    endpoint_url='https://mturk-requester-sandbox.us-east-1.amazonaws.com'
)

balance = mturk.get_account_balance()
print("Account balance (Sandbox):", balance['AvailableBalance'])
