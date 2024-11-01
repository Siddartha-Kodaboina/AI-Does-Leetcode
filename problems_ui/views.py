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

# Initialize AWS S3 and DynamoDB clients
s3 = boto3.client(
    's3',
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
    table = dynamodb.Table('leetcode-ai-questions')
    response = table.scan()
    problems = [item for item in response.get('Items', []) if item.get('uploaded_by') == 'sid']

    # Check if problems are still being processed
    processing_problems = []
    for problem in problems:
        s3_path = f"{problem['question_id']}/{problem['question_id']}.html"
        try:
            s3.head_object(Bucket=os.getenv('AWS_STORAGE_BUCKET_NAME'), Key=s3_path)
        except s3.exceptions.ClientError:
            processing_problems.append(problem)

    return render(request, 'problems_ui/user_problems.html', {
        'problems': problems,
        'processing_problems': processing_problems
    })

