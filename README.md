# LeetCode Question Generator 🚀

![Architecture Diagram Image]("./Architecture%20Diagram.png")

Transform interview discussion questions into fully-functional LeetCode-style problems with just one click! This platform allows users to create and practice coding problems by simply submitting descriptions from interview discussions.

## 🎯 Problem Statement
During FAANG interview preparation, developers often come across interesting problems in LeetCode discussion forums. However, these problems aren't available on the platform for practice. This project bridges that gap by automatically generating complete LeetCode-style questions from descriptions.

## ✨ Features
- **One-Click Question Generation**: Convert plain descriptions into formatted LeetCode problems
- **Complete Problem Environment**: Get test cases, solutions, and a coding interface
- **Mock Interview Experience**: Listen to AI-generated interview discussions
- **Automated Test Cases**: 25 test cases generated automatically
- **Optimal Solution**: Get a tester's solution for verification
- **Interactive UI**: Practice in a familiar LeetCode-like environment

## 🛠️ Technology Stack
- **Frontend & Backend**: Django
- **Databases**: 
  - Amazon DynamoDB (Metadata storage)
  - Amazon S3 (File storage)
- **Serverless**: AWS Lambda
- **AI/ML**: 
  - OpenAI GPT-4
  - Restack
- **Code Testing**: Judge0
- **Voice Generation**: MURF AI

## 🏗️ Architecture & Workflow

### 1. Question Creation Flow
1. **User Input**
   - User submits question description through UI
   - Backend receives description at `/create` endpoint

2. **Question Generation**
   - First GPT-4 call generates LeetCode-style description
   - Second GPT-4 call generates metadata:
     - Examples
     - Explanations
     - Constraints
     - Input/Output formats

3. **Content Generation**
   - Creates HTML file for question display
   - Generates unique question ID (UUID)
   - Uploads HTML to S3: `{S3Bucket}/{QID}/{QID}.html`
   - Stores metadata in DynamoDB:
     - Question title
     - Company tags
     - Difficulty level
     - Solution statistics

### 2. Test Cases Generation
1. **Script Creation**
   - GPT-4 generates test case script based on constraints
   - Uploads to S3: `{S3Bucket}/{QID}/generate_test_cases.py`

2. **Automated Generation**
   - S3 event triggers Lambda function
   - Lambda executes script 25 times
   - Generates test cases at: `{S3Bucket}/{QID}/input/testcase{i}.txt`

### 3. Solution Processing
1. **Tester Solution**
   - GPT-4 generates optimal solution
   - Uploads to S3: `{S3Bucket}/{QID}/tester_solution.py`

2. **Output Generation**
   - Lambda function triggered by solution upload
   - Runs solution against all test cases
   - Stores outputs at: `{S3Bucket}/{QID}/output/testcase{i}.txt`

### 4. Interview Simulation
1. **Conversation Generation**
   - GPT-4 generates interview dialogue in XML format
   - Includes:
     - Clarifying questions
     - Initial solution discussion
     - Complexity analysis
     - Optimal solution walkthrough

2. **Audio Processing**
   - Parses XML into separate dialogues
   - Generates speech using MURF AI
   - Creates complete interview audio
   - Uploads to S3: `{S3Bucket}/{QID}/interview_audio.mp3`

## 📂 S3 Bucket Structure
{S3Bucket}/{QID}/
├── {QID}.html
├── generate_test_cases.py
├── tester_solution.py
├── interview_audio.mp3
├── input/
│   ├── testcase1.txt
│   ├── testcase2.txt
│   └── ...
└── output/
├── testcase1.txt
├── testcase2.txt
└── ...

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- AWS Account
- OpenAI API Key
- MURF AI API Access
- Judge0 API Access

### Installation
1. Clone the repository
```bash
git clone https://github.com/yourusername/leetcode-question-generator.git
cd leetcode-question-generator
```

2. Install dependencies
```bash
pip install -r requirements.txt
```

3. Set up environment variables

```bash
cp .env.example .env
# Edit .env with your API keys and configurations
```

4. Run the application

```bash
python manage.py runserver
```
# 🙏 Acknowledgments

OpenAI for providing API credits during the hackathon
The LeetCode community for inspiration
All contributors and testers


Built with ❤️ during the OpenAI GPT-4 96-hour Hackathon



