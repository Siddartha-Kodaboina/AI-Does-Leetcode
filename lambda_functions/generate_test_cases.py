import boto3
import subprocess
import os

s3 = boto3.client('s3')

def download_script_from_s3(bucket_name, script_path):
    local_file_path = '/tmp/generate_test_cases.py'  # Temporary storage in Lambda

    # Try to download the script from S3
    print(f"Attempting to download from bucket: {bucket_name}, path: {script_path}")
    try:
        s3.download_file(bucket_name, script_path, local_file_path)
        print(f"Successfully downloaded {script_path} from S3")
    except Exception as e:
        print(f"Error downloading file: {e}")
        raise e

    return local_file_path


def lambda_handler(event, context):
    # Extracting the bucket name and object key (file path) from the S3 event
    try:
        # S3 event information is in the "Records" array
        s3_event = event['Records'][0]['s3']
        bucket_name = s3_event['bucket']['name']  # Bucket name from event
        script_path = s3_event['object']['key']   # Full path of the object in the bucket (key)
        
        print(f"Bucket: {bucket_name}")
        print(f"Script Path: {script_path}")

        # Extract the question_id from the file path (assuming it's the first part of the key)
        question_id = script_path.split('/')[0]  # Adjust based on your path structure
        print(f"Extracted question_id: {question_id}")

        # Step 1: Download the Python script from S3
        local_script = download_script_from_s3(bucket_name, script_path)

        # Step 2: Execute the downloaded Python script
        try:
            result = subprocess.run(['python3', local_script], capture_output=True, text=True, check=True)
            print("Script executed successfully")
            print(result.stdout)
        except subprocess.CalledProcessError as e:
            print(f"Error executing script: {e.stderr}")
            return {
                'statusCode': 500,
                'body': f"Error executing script: {e.stderr}"
            }
        
        return {
            'statusCode': 200,
            'body': "Test cases generated and uploaded to S3 successfully!"
        }

    except KeyError as e:
        print(f"Error processing event: {e}")
        return {
            'statusCode': 400,
            'body': "Failed to process event."
        }

