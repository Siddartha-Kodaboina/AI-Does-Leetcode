import boto3
import os
from django.shortcuts import render
import random

# Initialize DynamoDB and S3 clients
dynamodb = boto3.resource('dynamodb', region_name=os.getenv('AWS_REGION'))
s3 = boto3.client('s3', region_name=os.getenv('AWS_REGION'))
s3_bucket_name = os.getenv('AWS_STORAGE_BUCKET_NAME')

def audio_page(request):
    table = dynamodb.Table('leetcode-ai-questions')
    
    # Fetch all items and select a random one
    response = table.scan()
    items = response.get('Items', [])
    
    if not items:
        return render(request, 'audio_player/audio_page.html', {'error': 'No audio books found'})

    random_audio = random.choice(items)
    question_id = random_audio['question_id']
    audio_url = f"https://{s3_bucket_name}.s3.{os.getenv('AWS_REGION')}.amazonaws.com/{question_id}/interview_audio.mp3"

    # Fetch the HTML content from S3
    html_file_key = f"{question_id}/{question_id}.html"
    try:
        s3_response = s3.get_object(Bucket=s3_bucket_name, Key=html_file_key)
        html_content = s3_response['Body'].read().decode('utf-8')
    except Exception as e:
        html_content = None
        print(f"Error fetching HTML: {e}")

    # Fetch related audio books (up to 5 unique ones)
    related_audios = random.sample(items, min(5, len(items)))

    context = {
        'audio': {'title': random_audio['title'], 'audio_url': audio_url},
        'html_content': html_content,
        'related_audios': [{'title': item['title'], 'question_id': item['question_id']} for item in related_audios if item['question_id'] != question_id]
    }
    return render(request, 'audio_player/audio_page.html', context)
