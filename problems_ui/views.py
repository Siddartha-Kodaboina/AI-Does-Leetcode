from django.shortcuts import render
import boto3
import os

# Initialize DynamoDB resource
dynamodb = boto3.resource(
    'dynamodb',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    region_name=os.getenv('AWS_REGION')
)

def all_problems(request):
    # Fetch all problems from DynamoDB
    table = dynamodb.Table('leetcode-ai-questions')
    response = table.scan()  # Fetches all items in the table

    # Pass the problems to the template
    problems = response.get('Items', [])
    return render(request, 'problems_ui/all_problems.html', {'problems': problems})

def user_problems(request):
    # Fetch problems created by the user (in this case, user 'sid')
    table = dynamodb.Table('leetcode-ai-questions')
    response = table.scan()  # Fetch all items

    # Filter by the 'uploaded_by' field (assuming 'sid' is the logged-in user)
    problems = [item for item in response.get('Items', []) if item.get('uploaded_by') == 'sid']

    return render(request, 'problems_ui/user_problems.html', {'problems': problems})
