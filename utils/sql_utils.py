from schemas.sql_tables import Job, Candidate,Application,connect_to_postgres
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import ast

def store_candidate(candidate_info_dict):
    engine = connect_to_postgres()
    Session = sessionmaker(bind=engine)
    session = Session()

    print("================================STORE DATA===============================")

    print(candidate_info_dict)

    print("================================STORE DATA===============================")
    
    new_candidate = Candidate(
        first_name=candidate_info_dict['first_name'],
        last_name=candidate_info_dict['last_name'],
        email=candidate_info_dict["email"],
        phone=candidate_info_dict['phone'],
        resume_path=candidate_info_dict.get('resume_path'," "),
        linkedin_url=candidate_info_dict['linkedin_url'],
        github_url=candidate_info_dict['github_url'],
        portfolio_url=candidate_info_dict['portfolio_url'],
        current_position=candidate_info_dict['current_position'],
        current_company=candidate_info_dict["current_company"],
        location = candidate_info_dict["location"],
        created_at = datetime.now().replace(microsecond=0).isoformat() + "Z",
        updated_at = datetime.now().replace(microsecond=0).isoformat() + "Z",

    )
    session.add(new_candidate)
    session.commit()
    candidate_id = new_candidate.id
    
    session.close()
    return candidate_id

def submit_store_applications(application_dict,jd_id):

    engine = connect_to_postgres()
    Session = sessionmaker(bind=engine)
    session = Session()

    new_application = Application(
        candidate_id=application_dict.get("candidate_id",""),
        job_id=jd_id,
        job_title = application_dict.get("job_title",""),
        status="Applied",
        overall_score = application_dict.get("overall_score",""),
        technical_score = application_dict.get("technical_score",""),
        experience_score = application_dict.get("experience_score",""),
        education_score = application_dict.get("education_score",""),
        current_round = 0,
        weaviate_analysis_id = application_dict.get("weaviate_analysis_id",""),
        rejection_reason = application_dict.get("rejection_reason",""),
        created_at = datetime.now().replace(microsecond=0).isoformat() + "Z",
        updated_at = datetime.now().replace(microsecond=0).isoformat() + "Z"
    )

    session.add(new_application)
    session.commit()
    new_application_id = new_application.id
    
    session.close()
    return new_application_id

def extract_candidate_info(llm, candidate_resume_text):
    try:
        candidate_prompt = f"""
        Given the candidate resume text below, extract the following fields in a dictionary. 
        If the field doesn't exist or cannot be confidently determined, return an empty string.

        Return a pure Python dictionary text for the following fields:

        {{
            "first_name": "First name of the candidate",
            "last_name": "Last name of the candidate",
            "email": "Email address of the candidate",
            "phone": "Phone number",
            "linkedin_url": "LinkedIn URL",
            "github_url": "GitHub URL",
            "portfolio_url": "Portfolio/Website URL",
            "current_position": "Current Job Title",
            "current_company": "Current Company Name",
            "location": "Current Location"
        }}

        Resume:
        {candidate_resume_text}

        Only return the dictionary without any extra text or formatting.
        """

        candidate_info_str = llm.invoke(candidate_prompt)

        try:
            candidate_info = ast.literal_eval(candidate_info_str.content)
        except (SyntaxError, ValueError) as e:
            print(f"[extract_candidate_info] Error parsing candidate info: {e}")
            return None 

        #first_name = candidate_info.get("first_name", "").strip()
        #last_name = candidate_info.get("last_name", "").strip()
        #email = candidate_info.get("email", "").strip()

        first_name = candidate_info['first_name']
        last_name = candidate_info['last_name']
        email = candidate_info['email']

        # if not first_name or not last_name or not email:
        #     print(f"[extract_candidate_info] Missing critical fields: first_name='{first_name}', last_name='{last_name}', email='{email}'. Skipping candidate.")
        #     return None  


        candidate_id = store_candidate(candidate_info)
        return candidate_id

    except Exception as e:
        print(f"[extract_candidate_info] Unexpected Exception: {e}")
        return None
