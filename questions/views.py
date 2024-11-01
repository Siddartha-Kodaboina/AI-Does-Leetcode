from django.shortcuts import render, redirect
from django.http import JsonResponse
import requests
import os
import uuid
import boto3
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from pydub import AudioSegment
from .tasks import process_question_task
# Main view to handle form submissions
from .utils import (
    generate_question_with_gpt,
    generate_metadata_with_gpt,
    parse_metadata,
    generate_test_case_script_with_gpt,
    upload_question_to_s3,
    generate_optimal_solution_with_gpt,
    upload_test_case_script_to_s3,
    generate_interview_conversation,
    convert_text_to_audio,
    upload_audio_to_s3,
    generate_unique_question_id, 
    AWS_S3_BUCKET,
    store_question_metadata_in_dynamo
)

def create_question(request):
    if request.method == 'POST':
        # description = request.POST.get('description', '')
        # attachments = request.FILES.getlist('attachments')
        
        description = request.POST.get('description', '')
        attachments = request.FILES.getlist('attachments')
        file_ids = []

        # Upload attachments to OpenAI and get file IDs
        for attachment in attachments:
            file_id = upload_file_to_openai(attachment)
            file_ids.append(file_id)

        # Trigger the background task and get the task ID
        task = process_question_task.delay(description, file_ids)

        # Redirect to the 'user_problems' page
        return redirect('user_problems')

    return render(request, 'questions/create_question.html')
        
        
        
        # ----------------------------------------------------------------
    #     description = request.POST.get('description', '')
    #     attachments = request.FILES.getlist('attachments')
    #     file_ids = []

    #     # Upload attachments to OpenAI and get file IDs
    #     for attachment in attachments:
    #         file_id = upload_file_to_openai(attachment)
    #         file_ids.append(file_id)

    #     # Step 1: Generate LeetCode-style question using GPT-4
    #     generated_question = generate_question_with_gpt(description, file_ids)

    #     # Step 2: Generate metadata for the question using GPT-4
    #     generated_metadata = generate_metadata_with_gpt(generated_question)

    #     # Step 3: Parse the metadata
    #     metadata = parse_metadata(generated_metadata)

    #     # Generate unique ID for the question
    #     question_id = generate_unique_question_id()

    #     # Step 4: Format the question as HTML
    #     html_content, question_statement, example_1, example_2, input_format, output_format, constraints  = format_question_as_html(question_id, generated_question)

    #     # Step 5: Upload the HTML to S3
    #     s3_url = upload_question_to_s3(question_id, html_content)

    #     # Step 6: Store the metadata in DynamoDB
    #     meta_data_stored = store_question_metadata_in_dynamo(
    #         question_id=question_id,
    #         metadata=metadata
    #     )

    #     # Step 7: Generate the test case script using GPT-4o-mini
    #     python_script = generate_test_case_script_with_gpt(
    #         question_id=question_id,
    #         input_format=input_format,
    #         constraints=constraints,
    #         bucket_name=AWS_S3_BUCKET,
    #         test_cases_path=f"{question_id}/input"
    #     )

    #     # Step 8: Upload the generated Python script to S3
    #     test_case_script_url = upload_test_case_script_to_s3(question_id, python_script, "generate_test_cases")

    #     # Step 9: Generate the optimal solution using GPT-4o-mini
    #     optimal_solution = generate_optimal_solution_with_gpt(
    #         question_id=question_id,
    #         generated_question=generated_question,
    #         question_statement=question_statement,
    #         input_format=input_format,
    #         constraints=constraints,
    #         output_format=output_format,
    #         bucket_name=AWS_S3_BUCKET
    #     )

    #     # Step 10: Upload the optimal solution to S3
    #     tester_solution_url = upload_test_case_script_to_s3(question_id, optimal_solution, "tester_solution")
        
    #      # Step 11: Generate interview conversation and audio
    #     interview_conversation = generate_interview_conversation(generated_question)
    #     print(interview_conversation)
    #     audio_file_path = convert_text_to_audio(interview_conversation)
    #     audio_url = upload_audio_to_s3(audio_file_path, question_id)

    #     return JsonResponse({
    #         'status': 'success',
    #         's3_url': s3_url,
    #         'generated_question': generated_question,
    #         'meta_data_stored': meta_data_stored,
    #         'metadata': metadata,
    #         'test_case_script_url': test_case_script_url,
    #         'tester_solution_url': tester_solution_url,
    #         'audio_url': audio_url
    #     })

    # return render(request, 'questions/create_question.html')
