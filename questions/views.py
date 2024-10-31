from django.shortcuts import render
from django.http import JsonResponse
import requests
import os
import uuid
import boto3
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage

# Load your OpenAI API key and AWS credentials
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
AWS_S3_BUCKET = os.getenv('AWS_STORAGE_BUCKET_NAME')
UPLOAD_URL = "https://api.openai.com/v1/files"

# Initialize AWS S3 and DynamoDB clients
s3 = boto3.client(
    's3',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    region_name=os.getenv('AWS_REGION')
)

dynamodb = boto3.resource(
    'dynamodb',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    region_name=os.getenv('AWS_REGION')
)

# Function to upload file to OpenAI (image or text-based)
def upload_file_to_openai(file, purpose="assistants"):
    file_name = file.name
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
    }
    files = {
        'file': (file_name, file),  # Sending the file object directly
        'purpose': (None, purpose),
    }
    
    response = requests.post(UPLOAD_URL, headers=headers, files=files)
    if response.status_code == 200:
        return response.json()['id']  # Return the uploaded file's ID
    else:
        raise Exception(f"Error uploading file: {response.status_code}, {response.text}")

# Function to generate a unique question ID
def generate_unique_question_id():
    return str(uuid.uuid4())  # Generates a unique ID

# Function to generate question using GPT-4o chat model with file attachments
def generate_question_with_gpt(description, file_ids):
    base_prompt = f"""
    Create a LeetCode-style question based on the following problem description:

    {description}
    """
    if file_ids:
        base_prompt += "\nPlease take the following files into consideration for this task:\n"
        for file_id in file_ids:
            base_prompt += f"File ID: {file_id}\n"

    base_prompt += """
    Your output should include the following:
    
    1. Question Statement
    2. Example 1 (with detailed explanation)
    3. Example 2 (with detailed explanation)
    4. Input format: Describe input format details (line-separated, space-separated, etc.)
    5. Output format: Describe output format details
    6. Constraints: Limit constraints to 10^3
    """
    
    # Prepare chat model messages
    messages = [
        SystemMessage(content="You are an AI that generates LeetCode-style coding problems."),
        HumanMessage(content=base_prompt)
    ]

    # Use the OpenAI chat model for GPT-4
    chat = ChatOpenAI(api_key=OPENAI_API_KEY, model="gpt-4o")
    response = chat.invoke(messages)
    
    return response.content  # Return the raw text response

# Function to generate metadata for the question
def generate_metadata_with_gpt(question_content):
    metadata_prompt = f"""
    Based on the following LeetCode-style question, generate metadata for the question in the following format:
    
    <title> Title of the Question </title>
    <company> Company most likely to ask the question </company>
    <difficulty> Difficulty level (Easy, Medium, or Hard) </difficulty>

    Question content:
    {question_content}
    """

    # Prepare chat model messages for metadata
    messages = [
        SystemMessage(content="You are an AI that generates metadata for coding problems."),
        HumanMessage(content=metadata_prompt)
    ]

    # Use the OpenAI chat model for GPT-4
    chat = ChatOpenAI(api_key=OPENAI_API_KEY, model="gpt-4o")
    response = chat.invoke(messages)
    print(f"Generated metadata: {response}")
    
    return response.content

# Function to parse the metadata from the generated content
def parse_metadata(metadata_content):
    # Parse the title
    title_start = metadata_content.find("<title>") + len("<title>")
    title_end = metadata_content.find("</title>")
    title = metadata_content[title_start:title_end].strip()

    # Parse the company
    company_start = metadata_content.find("<company>") + len("<company>")
    company_end = metadata_content.find("</company>")
    company = metadata_content[company_start:company_end].strip()

    # Parse the difficulty
    difficulty_start = metadata_content.find("<difficulty>") + len("<difficulty>")
    difficulty_end = metadata_content.find("</difficulty>")
    difficulty = metadata_content[difficulty_start:difficulty_end].strip()

    return {
        "title": title,
        "company": company,
        "difficulty": difficulty
    }

# Function to store metadata in DynamoDB
def store_question_metadata_in_dynamo(question_id, metadata):
    try:
        table = dynamodb.Table('leetcode-ai-questions')
        table.put_item(
            Item={
                'question_id': question_id,
                'title': metadata['title'],
                'company': metadata['company'],
                'difficulty': metadata['difficulty'],
                'num_submissions': 0,  # Initial count of submissions
                'successful_submissions': 0,  # Initial count of successful submissions
                'uploaded_by': 'sid'  # Placeholder for now, replace with actual user data
            }
        )
        return True
    except Exception as e:
        print(f"Error storing metadata in DynamoDB: {e}")
        return False

# Function to format the question as HTML
def format_question_as_html(question_id, question_content):
    # Since question_content is a single string, we'll split it based on common markers like headers
    # Example, we'll extract the section by parsing the raw text content
    lines = question_content.split("\n")

    # Initialize placeholders for each section
    question_statement = ""
    example_1 = ""
    example_2 = ""
    input_format = ""
    output_format = ""
    constraints = ""

    # Parsing logic to extract sections
    current_section = None
    for line in lines:
        if "Question Statement" in line:
            current_section = "question_statement"
        elif "Example 1" in line:
            current_section = "example_1"
        elif "Example 2" in line:
            current_section = "example_2"
        elif "Input Format" in line:
            current_section = "input_format"
        elif "Output Format" in line:
            current_section = "output_format"
        elif "Constraints" in line:
            current_section = "constraints"
        elif current_section:
            # Append to the corresponding section
            if current_section == "question_statement":
                question_statement += line + "\n"
            elif current_section == "example_1":
                example_1 += line + "\n"
            elif current_section == "example_2":
                example_2 += line + "\n"
            elif current_section == "input_format":
                input_format += line + "\n"
            elif current_section == "output_format":
                output_format += line + "\n"
            elif current_section == "constraints":
                constraints += line + "\n"

    # Generate the HTML content from the parsed sections
    html_content = f"""
    <html>
    <head>
        <title>LeetCode AI Problem {question_id}</title>
    </head>
    <body>
        <h1>Question Statement</h1>
        <p>{question_statement.strip()}</p>
        
        <h2>Example 1</h2>
        <p>{example_1.strip()}</p>
        
        <h2>Example 2</h2>
        <p>{example_2.strip()}</p>
        
        <h2>Input Format</h2>
        <p>{input_format.strip()}</p>
        
        <h2>Output Format</h2>
        <p>{output_format.strip()}</p>
        
        <h2>Constraints</h2>
        <p>{constraints.strip()}</p>
    </body>
    </html>
    """
    return [html_content, question_statement.strip(), example_1.strip(), example_2.strip(), input_format.strip(), output_format.strip(), constraints.strip()]

# Function to upload the HTML question file to S3
def upload_question_to_s3(question_id, html_content):
    s3_file_path = f"{question_id}/{question_id}.html"

    try:
        s3.put_object(
            Bucket=os.getenv('AWS_STORAGE_BUCKET_NAME'),
            Key=s3_file_path,
            Body=html_content,
            ContentType='text/html'
        )
        return f"https://{os.getenv('AWS_STORAGE_BUCKET_NAME')}.s3.{os.getenv('AWS_REGION')}.amazonaws.com/{s3_file_path}"
    except Exception as e:
        print(f"Error uploading file to S3: {e}")
        return None

# Function to generate a Python script to create test cases using GPT-4o-mini
def generate_test_case_script_with_gpt(question_id, input_format, constraints, bucket_name, test_cases_path):
    """
    This function uses GPT-4o-mini to generate a robust Python script that generates test cases
    and uploads them to a specified S3 path. The script is designed to handle edge cases
    and include error handling.
    """
    test_case_prompt = f"""
    Create a robust Python script that generates 25 test cases based on the following input format 
    and constraints. The generated test cases should be saved to the provided S3 bucket path.

    Input Format:
    {input_format}

    Constraints:
    {constraints}

    The script should take the following parameters:
    - question_id: {question_id} - The unique ID for the question. 
    - bucket_name: {bucket_name} - The S3 bucket name where the test cases will be stored.
    - test_cases_path: {bucket_name}/{question_id}/input/testcaseX.txt -  The path in the S3 bucket where test case files should be saved (e.g., "question_id/input/").

    The script should:
    1. Generate 25 test cases following the input format and constraints.
    2. Handle edge cases, such as maximum and minimum input lengths, invalid inputs, etc.
    3. Save each test case in a text file (testcase1.txt, testcase2.txt, ..., testcase25.txt).
    4. Upload each test case to the S3 path: "bucket_name/question_id/input/testcaseX.txt".
    5. Ensure that temporary files (e.g., in the /tmp directory) are cleaned up after uploading to S3.
    6. Implement proper exception handling for S3 uploads and file creation.
    7. Ensure the script logs useful information, such as test case generation and upload success/failure.

    Example:
    For a string input of lowercase letters with a length constraint of 1 to 1000, generate random strings that follow this constraint.
    
    Additional Requirements:
    - Use the Python `boto3` library for uploading files to S3.
    - Write the test cases to the /tmp directory (for environments like AWS Lambda).
    - Catch any errors that may occur during file writing or S3 uploading and log them for troubleshooting.
    - Ensure the script is modular with functions that can be reused and tested independently.
    - Avoid unnecessary comments and explanations.

    Output Generation Format(I dont want any explanation at the beginning of the code or at the end of the code, I just want the code enclosed in code tags as mentioned below):
    "<code>python_code</code>"
    """

    # Prepare chat model messages for generating the Python script
    messages = [
        SystemMessage(content="You are an AI that generates Python scripts for generating test cases."),
        HumanMessage(content=test_case_prompt)
    ]

    # Use GPT-4o-mini to generate the Python script
    chat = ChatOpenAI(api_key=OPENAI_API_KEY, model="gpt-4o-mini")
    response = chat.invoke(messages)
    
    python_script = response.content
    python_script = python_script.replace("```python", "").replace("```", "").strip()
    python_script = python_script.replace("<code>", "").replace("</code>", "").strip()

    return python_script  # Return the generated Python script as a string

# Function to upload the generated Python test case script to S3
def upload_test_case_script_to_s3(question_id, python_script, file_name):
    """
    Upload the generated Python script to S3.
    """
    s3_file_path = f"{question_id}/{file_name}.py"

    try:
        s3.put_object(
            Bucket=os.getenv('AWS_STORAGE_BUCKET_NAME'),
            Key=s3_file_path,
            Body=python_script,
            ContentType='text/x-python'
        )
        return f"https://{os.getenv('AWS_STORAGE_BUCKET_NAME')}.s3.{os.getenv('AWS_REGION')}.amazonaws.com/{s3_file_path}"
    except Exception as e:
        print(f"Error uploading Python script to S3: {e}")
        return None


def generate_optimal_solution_with_gpt(question_id, generated_question, question_statement, input_format, constraints, output_format, bucket_name):
    """
    This function uses GPT-4o-mini to generate an optimal solution based on time complexity constraints
    and the input/output format described in the question.
    """
    optimal_solution_prompt = f"""
    Create an optimal and correct Python solution to the following problem statement, considering the constraints for time and space complexity.
    
    Complete Problem, examples, and constraints:
    {generated_question}

    The solution must:
    1. Take input according to the input format.
    2. Return output in the correct format.
    3. Handle the input/output inside the `__main__` function where:
       - The input should be read from `sys.stdin.read()`, which contains all the input lines.
       - The solution logic should be placed in a function that receives the input parameters and **must return** the result in all possible execution paths.
       - If no valid return value is found during the execution of the logic, return a default value at the end (e.g., `-1`, `None`, or an empty list, depending on the expected output format).
       - The solution returned from the function should be printed in the output format as per the problem.
       - The final output should be written to `sys.stdout`.
    4. The solution should be optimal based on the constraints:
       - If n > 10^9, the time complexity should be O(1).
       - If n == 10^9 or 10^8, the time complexity should be O(n).
       - If n == 10^5 or 10^6, the time complexity should be O(n log n).
       - If n <= 10^4, the time complexity should be O(n^2).
       - If n <= 10^3, the time complexity can be O(n^3).
       - If n < 16, the time complexity can be O(2^n).

    The generated code should follow this structure(just like leetcode):
    1. A function(s) with the business logic that **must return** the generated result to main in **all possible paths**.
    2. A `main()` function that reads input from `sys.stdin`, processes the input, calls the function, and fetches and writes the output to `sys.stdout`.
    
    The code should not include any additional explanations, comments, or print statements outside the solution itself.

    Output Format (I don't want any explanation at the beginning of the code or at the end of the code, I just want the code enclosed in code tags as mentioned below):
    "<code>python_solution</code>"
    """
    
    # Prepare the chat model messages for generating the solution
    messages = [
        SystemMessage(content="You are an AI that generates Python solutions for competitive DSA coding problems."),
        HumanMessage(content=optimal_solution_prompt)
    ]

    # Use GPT-4o-mini to generate the solution
    chat = ChatOpenAI(api_key=OPENAI_API_KEY, model="gpt-4o-mini")
    response = chat.invoke(messages)
    
    # Process the output to remove unnecessary tags
    python_solution = response.content
    python_solution = python_solution.replace("```python", "").replace("```", "").strip()
    python_solution = python_solution.replace("<code>", "").replace("</code>", "").strip()

    return python_solution

# Main view to handle form submissions
def create_question(request):
    if request.method == 'POST':
        description = request.POST.get('description', '')
        attachments = request.FILES.getlist('attachments')
        file_ids = []

        # Upload attachments to OpenAI and get file IDs
        for attachment in attachments:
            file_id = upload_file_to_openai(attachment)
            file_ids.append(file_id)

        # Step 1: Generate LeetCode-style question using GPT-4
        generated_question = generate_question_with_gpt(description, file_ids)

        # Step 2: Generate metadata for the question using GPT-4
        generated_metadata = generate_metadata_with_gpt(generated_question)

        # Step 3: Parse the metadata
        metadata = parse_metadata(generated_metadata)

        # Generate unique ID for the question
        question_id = generate_unique_question_id()

        # Step 4: Format the question as HTML
        html_content, question_statement, example_1, example_2, input_format, output_format, constraints  = format_question_as_html(question_id, generated_question)

        # Step 5: Upload the HTML to S3
        s3_url = upload_question_to_s3(question_id, html_content)

        # Step 6: Store the metadata in DynamoDB
        meta_data_stored = store_question_metadata_in_dynamo(
            question_id=question_id,
            metadata=metadata
        )

        # Step 7: Generate the test case script using GPT-4o-mini
        python_script = generate_test_case_script_with_gpt(
            question_id=question_id,
            input_format=input_format,
            constraints=constraints,
            bucket_name=AWS_S3_BUCKET,
            test_cases_path=f"{question_id}/input"
        )

        # Step 8: Upload the generated Python script to S3
        test_case_script_url = upload_test_case_script_to_s3(question_id, python_script, "generate_test_cases")

        # Step 9: Generate the optimal solution using GPT-4o-mini
        optimal_solution = generate_optimal_solution_with_gpt(
            question_id=question_id,
            generated_question=generated_question,
            question_statement=question_statement,
            input_format=input_format,
            constraints=constraints,
            output_format=output_format,
            bucket_name=AWS_S3_BUCKET
        )

        # Step 10: Upload the optimal solution to S3
        tester_solution_url = upload_test_case_script_to_s3(question_id, optimal_solution, "tester_solution")

        return JsonResponse({
            'status': 'success',
            's3_url': s3_url,
            'generated_question': generated_question,
            'meta_data_stored': meta_data_stored,
            'metadata': metadata,
            'test_case_script_url': test_case_script_url,
            'tester_solution_url': tester_solution_url
        })

    return render(request, 'questions/create_question.html')
