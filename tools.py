import weaviate
import uuid
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from schemas.sql_tables import Job,Candidate, Application, connect_to_postgres 
from utils.sql_utils import store_candidate, submit_store_applications,extract_candidate_info
from utils.weaviate_utils import fetch_jd_text_and_title,store_detailed_resume_analysis
from weaviate import Client
import smtplib
from email.mime.text import MIMEText
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
import requests
import os
import ast
import json
from langchain.schema import AIMessage
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv
load_dotenv()

def clean_llm_output(reasoning: str) -> str:
    """Clean LLM output by stripping ``` and ```python blocks."""
    reasoning = reasoning.strip()
    if reasoning.startswith("```"):
        reasoning = reasoning.split("```", 1)[1]  # Remove the first ```
    if reasoning.endswith("```"):
        reasoning = reasoning.rsplit("```", 1)[0]  # Remove the last ```
    return reasoning.strip()

import re

def extract_years_experience(text):
    match = re.search(r'(\d+(\.\d+)?)', text)
    if match:
        return float(match.group(1))
    return None  # or default value like 0.0

# def create_and_store_job_description(user_input, llm, weaviate_client):
    """
    Creates a full job description text using an LLM based on provided user input,
    stores the generated description and original details in a Weaviate 'JobDescription' collection,
    creates a related record in a SQL database, updates the Weaviate object with the SQL ID,
    and returns the Weaviate ID, SQL ID, and the generated description.

    Args:
        user_input (dict): A dictionary containing details like 'title', 'department',
                           'responsibilities' (list), 'requiredSkills' (list), etc.
                           Expected keys: 'title', 'department', 'responsibilities',
                           'requiredSkills', 'preferredSkills', 'minimumQualifications',
                           'experienceYears', 'employmentType', 'location', 'salaryRange',
                           'salaryMin', 'salaryMax', 'educationLevel'.
                           Note: 'salaryMin', 'salaryMax', 'educationLevel' are used for SQL.
        llm: An instance of a LangChain/CrewAI compatible LLM for text generation.
        weaviate_client (weaviate.WeaviateClient): An active Weaviate v4 client instance.

    Returns:
        dict: A dictionary containing 'weaviate_id' (str), 'job_id' (str, from SQL),
              and 'description' (LLM response object with content).
              Returns None or raises exception on failure (error handling in tool needs improvement).
    """
    weaviate_client.connect()

    
    try:
        prompt = f"""
            Write a professional job description: {user_input} for the role below. Include an overview, responsibilities, required and preferred qualifications, and working conditions.

            Title:
            Department:
            Responsibilities:
            Required Skills:
            Preferred Skills:
            Minimum Qualifications: 
            Experience Years:
            Location:
            Employment Type:
            Salary Range:
            Just return the job description as a dictionary format. Do not include storage instructions, code, or formatting.
            """

        
        full_description = llm.invoke(prompt)

        print("============================FUll DESCRIPTION===============================")

        if isinstance(full_description, AIMessage):

            print(full_description.content)

            user_input = json.loads(str(full_description.content))

        else:

            user_input = json.loads(str(full_description))    

        print(type(user_input['Title']))

        print("============================FUll DESCRIPTION===============================")

        weaviate_obj = {
            "title": user_input['Title'],
            "department": user_input['Department'],
            "fullDescription": user_input['Overview'],
            "responsibilities": user_input['Responsibilities'],
            "requiredSkills": user_input['Required Skills'],
            "preferredSkills": user_input['Preferred Skills'],
            "minimumQualifications": [q.strip() for q in str(user_input['Minimum Qualifications']).split('.') if q.strip()],
            "experienceYears": str(extract_years_experience(user_input['Experience Years'])),
            "employmentType": user_input['Employment Type'],
            "location": user_input['Location'],
            "salaryRange": user_input['Salary Range'],
            "createdAt": datetime.now().replace(microsecond=0).isoformat() + "Z",
            "updatedAt": datetime.now().replace(microsecond=0).isoformat() + "Z",
            "jobId": " "
        }

        print(f"Weaviate object: {weaviate_obj}")
        print(f"\n\n")
        collection = weaviate_client.collections.get("JobDescription")
        weaviate_id = collection.data.insert(weaviate_obj)
        print(f"weaviate id : {weaviate_id}")


        engine = connect_to_postgres()
        Session = sessionmaker(bind=engine)
        session = Session()

        print("======================================USER INPUT====================================")

        print(user_input)

        print("======================================USER INPUT====================================")

        new_job = Job(
            id=str(weaviate_id),
            title=user_input['Title'],
            department=user_input['Department'],
            weaviate_description_id=str(weaviate_id),
            employment_type=user_input['Employment Type'],
            location=user_input['Location'],
            # salary_min=user_input.get('salaryMin'),
            # salary_max=user_input.get('salaryMax'),
            required_experience_years=int(extract_years_experience(user_input['Experience Years'])),
            education_level=user_input['Minimum Qualifications'],
            status="Open"
        )
        session.add(new_job)
        session.commit()
        job_id = new_job.id
        session.close()

        collection.data.update(uuid = weaviate_id,properties = {
            "jobId": job_id
        })
        print(full_description)
        weaviate_client.close()
        return {
            "weaviate_id": weaviate_id,
            "job_id": job_id,
            "description": full_description
        }
    except Exception as e:
        weaviate_client.close()
        print(f"{e}")

import fitz
 
def extract_text_from_pdf(pdf_path):
    text = ""
    with fitz.open(pdf_path) as pdf:
        for page in pdf:
            text += page.get_text()
    return text

async def create_and_store_job_description(company_details, file_path, llm, weaviate_client):
    """
    Creates a full job description text using an LLM based on provided user input,
    stores the generated description and original details in a Weaviate 'JobDescription' collection,
    creates a related record in a SQL database, updates the Weaviate object with the SQL ID,
    and returns the Weaviate ID, SQL ID, and the generated description.
 
    Args:
        user_input (dict): A dictionary containing details like 'title', 'department',
                           'responsibilities' (list), 'requiredSkills' (list), etc.
                           Expected keys: 'title', 'department', 'responsibilities',
                           'requiredSkills', 'preferredSkills', 'minimumQualifications',
                           'experienceYears', 'employmentType', 'location', 'salaryRange',
                           'salaryMin', 'salaryMax', 'educationLevel'.
                           Note: 'salaryMin', 'salaryMax', 'educationLevel' are used for SQL.
        llm: An instance of a LangChain/CrewAI compatible LLM for text generation.
        weaviate_client (weaviate.WeaviateClient): An active Weaviate v4 client instance.
 
    Returns:
        dict: A dictionary containing 'weaviate_id' (str), 'job_id' (str, from SQL),
              and 'description' (LLM response object with content).
              Returns None or raises exception on failure (error handling in tool needs improvement).
    """
    weaviate_client.connect()
    pdf_content = extract_text_from_pdf(str(file_path))
    try:
        prompt = f"""
            Write a professional job description: {pdf_content} for the role below. Include an overview, responsibilities, required and preferred qualifications, and working conditions.
 
            Title:
            Department:
            Responsibilities:
            Required Skills:
            Preferred Skills:
            Minimum Qualifications:
            Experience Years:
            Location:
            Employment Type:
            Salary Range:
            Just return the job description as a dictionary format. Do not include storage instructions, code, or formatting.
            """
 
        full_description = llm.invoke(prompt)
 
        print("============================FUll DESCRIPTION===============================")
 
        if isinstance(full_description, AIMessage):
 
            print(full_description.content)
 
            user_input = json.loads(str(full_description.content))
 
        else:
 
            user_input = json.loads(str(full_description))    
 
        print(type(user_input['Title']))
 
        print("============================FUll DESCRIPTION===============================")
 
        print(company_details)

        weaviate_obj = {
            "title": company_details.get('title', user_input['Title']),
            "department": company_details.get('department', user_input['Department']),
            "fullDescription": user_input['Overview'],
            "responsibilities": user_input['Responsibilities'].append(company_details.get('responsibilities', [])),
            "requiredSkills": user_input['Required Skills'].append(company_details.get('required_skills', [])),
            "preferredSkills": user_input['Preferred Skills'].append(company_details.get('preferred_skills', [])),
            "minimumQualifications": company_details.get('qualification', [q.strip() for q in str(user_input['Minimum Qualifications']).split('.') if q.strip()]),
            "experienceYears": company_details.get('experience', str(extract_years_experience(user_input['Experience Years']))),
            "employmentType": company_details.get('employment_type', user_input['Employment Type']),
            "location":  company_details.get('location', user_input['Location']),
            "salaryRange": company_details.get('salary_range', user_input['Salary Range']),
            "createdAt": datetime.now().replace(microsecond=0).isoformat() + "Z",
            "updatedAt": datetime.now().replace(microsecond=0).isoformat() + "Z",
            "jobId": " "
        }
 
        print(f"Weaviate object: {weaviate_obj}")
        print(f"\n\n")
        collection = weaviate_client.collections.get("JobDescription")
        weaviate_id = collection.data.insert(weaviate_obj)
        print(f"weaviate id : {weaviate_id}")
 
 
        engine = connect_to_postgres()
        Session = sessionmaker(bind=engine)
        session = Session()
 
        print("======================================USER INPUT====================================")
 
        print(user_input)
 
        print("======================================USER INPUT====================================")
 
        new_job = Job(
            id=str(weaviate_id),
            title=user_input['Title'],
            department=user_input['Department'],
            weaviate_description_id=str(weaviate_id),
            employment_type=user_input['Employment Type'],
            location=user_input['Location'],
            # salary_min=user_input.get('salaryMin'),
            # salary_max=user_input.get('salaryMax'),
            required_experience_years=int(extract_years_experience(user_input['Experience Years'])),
            education_level=user_input['Minimum Qualifications'],
            status="Open"
        )
        session.add(new_job)
        session.commit()
        job_id = new_job.id
        print("===========================JOBID==========================")
        print(job_id)
        print("===========================JOBID==========================")
        session.close()
 
        collection.data.update(uuid = weaviate_id,properties = {
            "jobId": job_id
        })
        print(full_description)
        weaviate_client.close()
        if job_id:
            return {
                "weaviate_id": weaviate_id,
                "job_id": job_id,
                "description": full_description
            }
    except Exception as e:
        weaviate_client.close()
        print(f"{e}")

def analyze_cv_resume_given_jd(candidate_resume_text,jd,llm,weaviate_client):
    candidate_id = extract_candidate_info(llm,candidate_resume_text)
    

    analysis_query = f"""
    Analyze this candidate's fit for the job by comparing their resume to the job description.

    Resume:
    {candidate_resume_text}

    Job Description:
    {jd}

    Return a detailed analysis as a Python dictionary. Do not include any markdown formatting, quotes, or explanatory text - only return valid Python code that could be parsed with json.loads() or ast.literal_eval().

    {{
    "overallAssessment": "Comprehensive analysis of overall fit with detailed reasoning",
    "skillMatchAnalysis": "Detailed comparison of candidate skills vs. job requirements with specific examples",
    "experienceRelevance": "Analysis of relevance of candidate's experience to the position",
    "educationFitAnalysis": "Analysis of how the candidate's education aligns with requirements",
    "strengths": "3-5 key strengths relevant to this specific role",
    "weaknesses": "2-3 areas where the candidate doesn't meet job requirements",
    "skillGaps": "Specific technical or soft skills mentioned in job description but missing from resume",
    "recommendedQuestions": "3 targeted interview questions based on resume gaps or experience verification",
    "overall_score": 0-100 comprehensive fit score,
    "technical_score": 0-100 score for technical skill match,
    "experience_score": 0-100 score for relevant experience,
    "education_score": 0-100 score for education requirements match,
    "potentialFlags": "Potential concerns or areas needing follow-up",
    "matchedSkills": ["list", "of", "skills", "that", "match", "job", "requirements"],
    "recommendationLevel": "One of: Strong Yes, Yes, Maybe, No, Strong No"
    }}

    """

    reasoning = llm.invoke(analysis_query)
    reasoning = reasoning.content
    print(reasoning)
    resume_analysis = ast.literal_eval(reasoning)

    print("============================RESUME ANALYSIS==============================")

    print(resume_analysis)

    print("============================RESUME ANALYSIS==============================")

    application_object = {
        "candidate_id": candidate_id,
        "job_id": "c0b982b0-744d-489c-ae91-38eedd559adf",
        "status": "Applied",
        "overall_score": float(resume_analysis["overall_score"]),
        "technical_score": float(resume_analysis["technical_score"]),
        "experience_score": float(resume_analysis["experience_score"]),
        "education_score": float(resume_analysis["education_score"]),
        "current_round": 0,
        #"weaviate_analysis_id": wv_resume_analysis_id,
        "rejection_reason": "This is the candidate's weakness: " + str(resume_analysis["weaknesses"][0]) + ". This is the skill gaps: " + str(resume_analysis["skillGaps"][0])

    }
    application_id = submit_store_applications(application_object,"c0b982b0-744d-489c-ae91-38eedd559adf")


    detailed_resume_reasoning = {
        "candidateId": str(candidate_id),
        "jobId": "c0b982b0-744d-489c-ae91-38eedd559adf",
        "applicationId": str(application_id),
        "overallAssessment": resume_analysis["overallAssessment"],
        "skillMatchAnalysis": resume_analysis["skillMatchAnalysis"],
        "experienceRelevance": resume_analysis["experienceRelevance"],
        "educationFitAnalysis": resume_analysis["educationFitAnalysis"],
        "strengths": resume_analysis["strengths"],
        "weaknesses": resume_analysis["weaknesses"],
        "skillGaps": [str(item) for item in resume_analysis["skillGaps"]],
        "recommendedQuestions": resume_analysis["recommendedQuestions"],
        "fitScore": int(resume_analysis["overall_score"]),
        "technicalScore": int(resume_analysis["technical_score"]),
        "experienceScore": int(resume_analysis["experience_score"]),
        "potentialFlags": str([resume_analysis["potentialFlags"]]),
        "matchedSkills": resume_analysis["matchedSkills"],
        "recommendationLevel": resume_analysis["recommendationLevel"],
        "analysisDate": datetime.now().replace(microsecond=0).isoformat() + "Z"
    }

    wv_resume_analysis_id = store_detailed_resume_analysis(detailed_resume_reasoning,weaviate_client)
    print(wv_resume_analysis_id)


def analyze_cv_resume(candidate_resume_text, jd_id, llm, weaviate_client):
    weaviate_client.connect()
    jd_text, job_title = fetch_jd_text_and_title(jd_id, weaviate_client)
    # print(f"jd text: {jd_text}")
    # print(f"job title: {job_title}")
    candidate_id = extract_candidate_info(llm, candidate_resume_text)
    if not candidate_id:
        print(f"Error in analyze cv resume: couldn't parse")
        return

    analysis_query = f"""
    Analyze this candidate's fit for the job by comparing their resume to the job description.

    Resume:
    {candidate_resume_text}

    Job Description:
    {jd_text}

    Return ONLY a pure Python dictionary (no markdown, no quotes, no ```python code blocks).

    {{
    "overallAssessment": "Comprehensive analysis of overall fit with detailed reasoning",
    "skillMatchAnalysis": "Detailed comparison of candidate skills vs. job requirements with specific examples",
    "experienceRelevance": "Analysis of relevance of candidate's experience to the position",
    "educationFitAnalysis": "Analysis of how the candidate's education aligns with requirements",
    "strengths": "3-5 key strengths relevant to this specific role",
    "weaknesses": "2-3 areas where the candidate doesn't meet job requirements",
    "skillGaps": "Specific technical or soft skills mentioned in job description but missing from resume",
    "recommendedQuestions": "3 targeted interview questions based on resume gaps or experience verification",
    "overall_score": 0-100 comprehensive fit score,
    "technical_score": 0-100 score for technical skill match,
    "experience_score": 0-100 score for relevant experience,
    "education_score": 0-100 score for education requirements match,
    "potentialFlags": "Potential concerns or areas needing follow-up",
    "matchedSkills": ["list", "of", "skills", "that", "match", "job", "requirements"],
    "recommendationLevel": "One of: Strong Yes, Yes, Maybe, No, Strong No"
    }}
    """

    # Step 1: Call LLM
    reasoning_response = llm.invoke(analysis_query)
    reasoning = reasoning_response.content
    print("Raw LLM Output:", reasoning)

    # Step 2: Clean the LLM output
    reasoning_cleaned = clean_llm_output(reasoning)

    # Step 3: Safely parse it
    try:
        resume_analysis = ast.literal_eval(reasoning_cleaned)
    except Exception as e:
        print("Error parsing LLM reasoning:", e)
        raise ValueError("Invalid LLM reasoning format") from e

    print("============================RESUME ANALYSIS==============================")

    print(resume_analysis)

    print("============================RESUME ANALYSIS==============================")


    # Step 4: Prepare application object
    application_object = {
        "candidate_id": candidate_id,
        "job_id": jd_id,
        "job_title": job_title,
        "status": "Applied",
        "overall_score": float(resume_analysis["overall_score"]),
        "technical_score": float(resume_analysis["technical_score"]),
        "experience_score": float(resume_analysis["experience_score"]),
        "education_score": float(resume_analysis["education_score"]),
        "current_round": 0,
        #"weaviate_analysis_id": wv_resume_analysis_id,
        "rejection_reason": "This is the candidate's weakness: " + (str(resume_analysis["weaknesses"][0]) if resume_analysis.get("weaknesses") and len(resume_analysis["weaknesses"]) > 0 else "None provided") + ". This is the skill gaps: " + (str(resume_analysis["skillGaps"][0]) if resume_analysis.get("skillGaps") and len(resume_analysis["skillGaps"]) > 0 else "None identified")
    }

    # Step 5: Store application
    application_id = submit_store_applications(application_object, jd_id)

    # Step 6: Prepare and store detailed reasoning
    detailed_resume_reasoning = {
        "candidateId": str(candidate_id),
        "jobId": jd_id,
        "applicationId": str(application_id),
        "overallAssessment": resume_analysis["overallAssessment"],
        "skillMatchAnalysis": resume_analysis["skillMatchAnalysis"],
        "experienceRelevance": resume_analysis["experienceRelevance"],
        "educationFitAnalysis": resume_analysis["educationFitAnalysis"],
        "strengths": resume_analysis["strengths"],
        "weaknesses": resume_analysis["weaknesses"],
        "skillGaps": [str(item) for item in resume_analysis["skillGaps"]],
        "recommendedQuestions": resume_analysis["recommendedQuestions"],
        "fitScore": int(resume_analysis["overall_score"]),
        "technicalScore": int(resume_analysis["technical_score"]),
        "experienceScore": int(resume_analysis["experience_score"]),
        "potentialFlags": [resume_analysis["potentialFlags"]],
        "matchedSkills": resume_analysis["matchedSkills"],
        "recommendationLevel": resume_analysis["recommendationLevel"],
        "analysisDate": datetime.now().replace(microsecond=0).isoformat() + "Z"
    }

    wv_resume_analysis_id = store_detailed_resume_analysis(detailed_resume_reasoning, weaviate_client)
    print("Stored Weaviate Resume Analysis ID:", wv_resume_analysis_id)


    weaviate_client.close()

    return wv_resume_analysis_id

    
def send_email(to_email, subject, body):
    if to_email and "@" in to_email:
      msg = MIMEText(body, "plain")
      msg["Subject"] = subject
      msg["From"] = os.getenv("GMAIL_USER")
      msg["To"] = to_email

      with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(os.getenv("GMAIL_USER"), os.getenv("GMAIL_APP_PASSWORD"))
        server.sendmail(os.getenv("GMAIL_USER"), to_email, msg.as_string())
    else:
        print(f"Invalid email address: {to_email}")   

def create_calendar_event(candidate_email, date_str, time_str):
    """
    Schedule an event on the given date and time (in local timezone).
    - date_str: 'YYYY-MM-DD'
    - time_str: 'HH:MM' (24h format)
    """
    from dateutil import parser

    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", os.getenv("SCOPES").split(","))

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", os.getenv("SCOPES").split(","))
            creds = flow.run_local_server(port=0)
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    try:
        service = build("calendar", "v3", credentials=creds)

        # Parse provided date and time into datetime object
        start_time = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
        end_time = start_time + timedelta(hours=1)

        request_id = f"interview-{int(datetime.now().timestamp())}"

        event = {
            "summary": "Interview",
            "location": "Online",
            "description": "Interview for shortlisted candidates",
            "start": {
                "dateTime": start_time.isoformat(),
                "timeZone": os.getenv("TIMEZONE"),
            },
            "end": {
                "dateTime": end_time.isoformat(),
                "timeZone": os.getenv("TIMEZONE"),
            },
            "attendees": [
                {"email": os.getenv("GMAIL_USER")},
                {"email": candidate_email}
            ],
            "conferenceData": {
                "createRequest": {
                    "requestId": request_id,
                    "conferenceSolutionKey": {"type": "hangoutsMeet"},
                }
            },
            "reminders": {"useDefault": True},
        }

        created_event = service.events().insert(
            calendarId="primary",
            body=event,
            conferenceDataVersion=1
        ).execute()

        return created_event.get("hangoutLink"), start_time.strftime("%Y-%m-%d %H:%M")

    except HttpError as error:
        print(f"An error occurred: {error}")
        return None, None