import boto3
import subprocess
import os
import logging

# Initialize boto3 client for S3
s3 = boto3.client('s3')

# Setup logger for better debugging and information tracking
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def download_file_from_s3(bucket_name, file_key, local_file_path):
    """Download file from S3 to the local Lambda environment."""
    try:
        logger.info(f"Downloading {file_key} from bucket {bucket_name} to {local_file_path}")
        s3.download_file(bucket_name, file_key, local_file_path)
        logger.info(f"Successfully downloaded {file_key}")
    except Exception as e:
        logger.error(f"Error downloading {file_key} from S3: {str(e)}")
        raise e

def upload_file_to_s3(bucket_name, file_key, local_file_path):
    """Upload file from local Lambda environment to S3."""
    try:
        logger.info(f"Uploading {file_key} to bucket {bucket_name}")
        s3.upload_file(local_file_path, bucket_name, file_key)
        logger.info(f"Successfully uploaded {file_key}")
    except Exception as e:
        logger.error(f"Error uploading {file_key} to S3: {str(e)}")
        raise e

def run_tester_solution(local_script, input_data):
    """Run the tester solution and capture its output."""
    try:
        logger.info("Running tester solution.")
        process = subprocess.run(
            ['python3', local_script],
            input=input_data,
            text=True,
            capture_output=True,
            check=True
        )
        logger.info("Script executed successfully.")
        return process.stdout.strip()
    except subprocess.CalledProcessError as e:
        logger.error(f"Error executing script: {e.stderr}")
        raise e

def lambda_handler(event, context):
    # S3 bucket details
    try:
        s3_event = event['Records'][0]['s3']
        bucket_name = s3_event['bucket']['name']  # Bucket name from event
        script_path = s3_event['object']['key']   # Full path of the object in the bucket (key)

        print(f"Bucket: {bucket_name}")
        print(f"Script Path: {script_path}")

        # Extract the question_id from the file path (assuming it's the first part of the key)
        question_id = script_path.split('/')[0]  # Adjust based on your path structure
        print(f"Extracted question_id: {question_id}")
        # bucket_name = event['bucket_name']
        # question_id = event['question_id']
        
        # Number of test cases (assuming fixed to 25 as mentioned)
        total_test_cases = 25

        # Paths for S3 and Lambda temp storage
        script_s3_path = f"{question_id}/tester_solution.py"
        local_script_path = '/tmp/tester_solution.py'

        # Step 1: Download the tester solution from S3
        logger.info("Starting process to download tester solution.")
        download_file_from_s3(bucket_name, script_s3_path, local_script_path)

        # Iterate through each test case
        for test_case_num in range(1, total_test_cases + 1):
            input_s3_path = f"{question_id}/input/testcase{test_case_num}.txt"
            output_s3_path = f"{question_id}/output/testcase{test_case_num}.txt"

            local_input_path = f'/tmp/input_testcase{test_case_num}.txt'
            local_output_path = f'/tmp/output_testcase{test_case_num}.txt'

            logger.info(f"Processing test case {test_case_num}")

            # Step 2: Download the input file from S3
            download_file_from_s3(bucket_name, input_s3_path, local_input_path)

            # Read the input data from the local file
            with open(local_input_path, 'r') as input_file:
                input_data = input_file.read()
                logger.info(f"Read input data for test case {test_case_num}")

            # Step 3: Run the tester solution with input
            try:
                logger.info(f"Running tester solution for test case {test_case_num}")
                output_data = run_tester_solution(local_script_path, input_data)
                logger.info(f"Tester solution ran successfully for test case {test_case_num}")
            except Exception as e:
                logger.error(f"Error while running solution for test case {test_case_num}: {str(e)}")
                return {
                    'statusCode': 500,
                    'body': f"Error running solution for test case {test_case_num}: {str(e)}"
                }

            # Step 4: Write the output data to a local file
            with open(local_output_path, 'w') as output_file:
                output_file.write(output_data)
                logger.info(f"Wrote output data for test case {test_case_num}")

            # Step 5: Upload the output file to S3
            upload_file_to_s3(bucket_name, output_s3_path, local_output_path)
            logger.info(f"Uploaded output for test case {test_case_num} to {output_s3_path}")

        # All test cases processed successfully
        return {
            'statusCode': 200,
            'body': f"All {total_test_cases} test cases executed successfully and outputs saved to S3."
        }
    except KeyError as e:
        print(f"Error processing event: {e}")
        return {
            'statusCode': 400,
            'body': "Failed to process event."
        }

