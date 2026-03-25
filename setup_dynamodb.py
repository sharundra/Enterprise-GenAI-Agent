import boto3
import os
from dotenv import load_dotenv

load_dotenv()

def populate_dynamodb():
    print("Connecting to DynamoDB...")
    # Initialize the DynamoDB resource
    dynamodb = boto3.resource('dynamodb', region_name=os.getenv("AWS_DEFAULT_REGION"))
    table = dynamodb.Table('employee_balances')

    dummy_data =[
        {'employee_id': 101, 'name': 'Alice Smith', 'department': 'Engineering', 'leave_days_remaining': 15},
        {'employee_id': 102, 'name': 'Bob Jones', 'department': 'Marketing', 'leave_days_remaining': 5},
        {'employee_id': 103, 'name': 'Charlie Brown', 'department': 'HR', 'leave_days_remaining': 22},
        {'employee_id': 104, 'name': 'Diana Prince', 'department': 'Engineering', 'leave_days_remaining': 30}
    ]

    print("Inserting data...")
    for item in dummy_data:
        table.put_item(Item=item)
        print(f"Inserted: {item['name']}")

    print("Successfully populated DynamoDB!")

if __name__ == "__main__":
    populate_dynamodb()