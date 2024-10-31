import base64
import requests
import json
import boto3
import logging
import os
from django.http import JsonResponse
from django.shortcuts import render
from botocore.exceptions import NoCredentialsError

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize S3 client
s3 = boto3.client(
    's3',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    region_name=os.getenv('AWS_REGION')
)

# RapidAPI configuration for Judge0
RAPIDAPI_KEY = os.getenv('RAPIDAPI_KEY')
JUDGE0_API_URL = "https://judge0-ce.p.rapidapi.com/submissions"

def fetch_s3_file(bucket_name, key):
    """Helper function to fetch file content from S3"""
    try:
        logger.info(f"Fetching file from S3: bucket={bucket_name}, key={key}")
        response = s3.get_object(Bucket=bucket_name, Key=key)
        content = response['Body'].read().decode('utf-8')
        logger.info(f"Successfully fetched file from S3: {key}")
        return content
    except Exception as e:
        logger.error(f"Error fetching file from S3: {str(e)}")
        return None

def problem_detail(request, question_id):
    """Render the problem detail page"""
    # Fetch the problem metadata from DynamoDB
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('leetcode-ai-questions')
    response = table.get_item(Key={'question_id': question_id})
    problem = response.get('Item', {})

    # Fetch the HTML file from S3
    s3_bucket_name = 'leetcode-ai-problems'  # replace with your actual S3 bucket name
    html_file_key = f"{question_id}/{question_id}.html"  # path to the HTML file in S3

    try:
        response = s3.get_object(Bucket=s3_bucket_name, Key=html_file_key)
        html_content = response['Body'].read().decode('utf-8')  # Read HTML content from S3
    except NoCredentialsError:
        return render(request, 'problems/problem_detail.html', {
            'problem': problem,
            'error': "Error: Unable to fetch the HTML file from S3."
        })

    return render(request, 'problems/problem_detail.html', {
        'problem': problem,
        'html_content': html_content  # Pass the HTML content to the template
    })

def run_code(request, question_id):
    """Run user code against test cases stored in S3 and return results"""
    if request.method == 'POST':
        logger.info(f"Received request to run code for question_id: {question_id}")

        # Get code and language from the POST request
        try:
            body = json.loads(request.body)
            source_code = body.get('source_code').strip()
            language = body.get('language')
            logger.info(f"Source code and language received. Language: {language}")
        except Exception as e:
            logger.error(f"Error reading request body: {str(e)}")
            return JsonResponse({'error': 'Invalid request body'}, status=400)

        # Check for default placeholder and remove it
        if source_code.startswith("# Write your code here"):
            source_code = source_code.replace("# Write your code here", "").strip()

        # Convert language to Judge0 language_id
        language_id = {
            'python': 71,
            'javascript': 63,
            'cpp': 54,
            'c': 50,
            'java': 62
        }.get(language, 71)  # Default to Python if not specified
        logger.info(f"Judge0 language ID for selected language: {language_id}")

        headers = {
            'content-type': "application/json",
            'x-rapidapi-host': "judge0-ce.p.rapidapi.com",
            'x-rapidapi-key': RAPIDAPI_KEY
        }

        total_test_cases = 10  # Modify this for the correct number of test cases
        results = []

        for i in range(1, total_test_cases + 1):
            # Fetch the input test case from S3
            input_key = f"{question_id}/input/testcase{i}.txt"
            expected_output_key = f"{question_id}/output/testcase{i}.txt"

            input_data = fetch_s3_file('leetcode-ai-problems', input_key)
            expected_output = fetch_s3_file('leetcode-ai-problems', expected_output_key)

            if input_data is None or expected_output is None:
                logger.error(f"Test case {i} missing in S3")
                return JsonResponse({'error': f"Test case {i} missing in S3"}, status=500)

            # Base64 encode the input data (stdin)
            encoded_input = base64.b64encode(input_data.encode('utf-8')).decode('utf-8')

            # Prepare the payload for Judge0 with input data
            payload = {
                "language_id": language_id,
                "source_code": source_code,  # Send source code as plain text
                "stdin": encoded_input,
                "base64_encoded": False,  # No base64 encoding for code
                "wait": True  # Wait for immediate result
            }

            logger.info(f"Submitting code to Judge0 for test case {i}")
            response = requests.post(JUDGE0_API_URL, json=payload, headers=headers)
            logger.info(f"Response status code from Judge0: {response.status_code}")
            logger.info(f"Response body from Judge0: {response.text}")

            if response.status_code == 201:
                submission_result = response.json()
                token = submission_result['token']
                result_url = f"{JUDGE0_API_URL}/{token}"
                logger.info(f"Fetching result from Judge0 for token: {token}")

                result_response = requests.get(result_url, headers=headers)
                logger.info(f"Judge0 result fetch status: {result_response.status_code}")
                logger.info(f"Judge0 result response: {result_response.text}")

                if result_response.status_code == 200:
                    judge0_result = result_response.json()

                    # Handle missing stdout (runtime error or other issues)
                    stdout = judge0_result.get('stdout', None)
                    if stdout:
                        actual_output = stdout.strip()
                    else:
                        actual_output = "No output or Runtime Error"
                        logger.error(f"No stdout for test case {i}: {judge0_result.get('stderr', '')}")

                    expected_output = expected_output.strip()

                    result = {
                        'test_case': i,
                        'input': input_data,  # Add test case input to the result
                        'expected': expected_output,
                        'actual': actual_output,
                        'status': judge0_result.get('status', {}).get('description', 'Unknown'),
                        'stderr': judge0_result.get('stderr', ''),
                        'result': 'Passed' if actual_output == expected_output else 'Failed'
                    }

                    results.append(result)
                else:
                    logger.error(f"Failed to fetch result from Judge0 for token {token}")
                    return JsonResponse({'error': 'Failed to fetch result from Judge0'}, status=500)

            else:
                logger.error(f"Failed to submit code to Judge0 for test case {i}")
                return JsonResponse({'error': 'Failed to submit code to Judge0'}, status=500)

        logger.info(f"All test cases processed for question_id: {question_id}")
        return JsonResponse({'test_case_results': results}, safe=False)

    else:
        logger.error(f"Invalid request method: {request.method}")
        return JsonResponse({'error': 'Invalid request method'}, status=400)
