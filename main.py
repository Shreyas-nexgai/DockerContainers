from crewai import Task, Crew, Agent, Process
from langchain_openai import AzureChatOpenAI
from schemas.sql_tables import Job,Candidate, Application, connect_to_postgres 
from sqlalchemy.orm import sessionmaker
from tools import create_and_store_job_description, analyze_cv_resume_given_jd, analyze_cv_resume
from schemas.jobDescriptions_wv import connect_to_local_weaviate
from agents import llm, job_description_writer
import os
from pathlib import Path
from pypdf import PdfReader
from llm_routing import router
from datetime import datetime, timedelta
from tools import send_email
from fastapi import FastAPI, Form 
from pydantic import BaseModel
from typing import List
import requests
# from crewai.tools import tool
app = FastAPI()

from fastapi.middleware.cors import CORSMiddleware
 
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

job_input = {
    "title": "Machine Learning Engineer (mid)",
    "department": "AI",
    "responsibilities": ["Fine Tune ML models", "Collaborate with data scientists"],
    "requiredSkills": ["Python", "Keras"],
    "preferredSkills": ["Docker", "OpenStack"],
    "minimumQualifications": ["Master's in Computer Science"],
    "experienceYears": 4,
    "employmentType": "Full-time",
    "location": "Remote",
    "salaryRange": "$100k - $130k",
    "salaryMin": 100000,
    "salaryMax": 130000,
    "educationLevel": "Master's"
}

resume_1 = """

        MICHAEL RODRIGUEZ
    📍 Austin, TX | 📧 michael.rodriguez@example.com | 📞 (512) 987-6543 | 💻 github.com/michaelrodriguez | linkedin.com/in/michaelrodriguez

    💼 PROFESSIONAL SUMMARY
    Passionate Full Stack Developer with 5+ years of experience building dynamic web platforms and microservices. Skilled at designing intuitive user experiences and optimizing backend performance. Specialized in JavaScript, Python, and scalable cloud deployments.

    🛠️ TECHNICAL SKILLS
    Languages: JavaScript (React, Node.js), Python, Go, SQL
    Frameworks/Libraries: React, Next.js, FastAPI, Express
    Databases: PostgreSQL, DynamoDB, Redis
    Tools & Platforms: AWS (ECS, Lambda, DynamoDB), Kubernetes, GitHub Actions
    Testing: Jest, Mocha, Cypress
    Other: REST APIs, GraphQL, Serverless, Agile/Scrum

    👨‍💻 PROFESSIONAL EXPERIENCE
    Senior Software Engineer
    CloudHaven Solutions | Austin, TX
    March 2022 – Present

    Designed and deployed serverless REST APIs using AWS Lambda and API Gateway, reducing costs by 20%.

    Led migration of core app frontend to Next.js, improving page load speed by 35%.

    Implemented real-time notifications using WebSockets and Redis Pub/Sub.

    Software Developer
    Innovex Systems | Remote
    August 2018 – February 2022

    Built modular React components for an internal dashboard managing 50k+ customer records.

    Developed microservices with FastAPI and PostgreSQL to support new billing features.

    🎓 EDUCATION
    B.S. in Computer Science
    University of Texas at Austin
    Graduated: 2018

    🏆 PROJECTS
    TravelTrackr – Travel planning web app with React, FastAPI, and PostgreSQL

    LivePolls – Real-time polling app using Go, WebSockets, and MongoDB Atlas

    💬 CERTIFICATIONS
    AWS Certified Solutions Architect – Associate

"""

resume_2 = """

        EMILY CHEN
    📍 Seattle, WA | 📧 emily.chen@example.com | 📞 (206) 123-4567 | 💻 github.com/emilychen | linkedin.com/in/emilychen

    💼 PROFESSIONAL SUMMARY
    Software Engineer specializing in backend systems, data engineering, and distributed computing. 4+ years of experience building highly available systems and stream processing pipelines at scale.

    🛠️ TECHNICAL SKILLS
    Languages: Python, Java, Scala, SQL
    Frameworks/Libraries: Django, Spring Boot, Apache Spark
    Databases: MySQL, Cassandra, BigQuery
    Tools & Platforms: Docker, Kubernetes, Airflow, AWS (EMR, Redshift)
    Testing: JUnit, PyTest
    Other: REST APIs, Kafka, ETL Pipelines, Agile/Scrum

    👨‍💻 PROFESSIONAL EXPERIENCE
    Backend Engineer
    DataSphere Inc. | Seattle, WA
    September 2020 – Present

    Designed scalable ETL pipelines using Apache Airflow and AWS Glue, reducing processing time by 30%.

    Developed high-throughput REST APIs in Spring Boot for real-time data ingestion.

    Built Spark jobs for batch and stream processing, handling 5TB daily.

    Data Engineer
    InfoWorks | Remote
    July 2018 – August 2020

    Developed BigQuery ETL jobs and integrated with Google Cloud Storage for an ad-tech platform.

    🎓 EDUCATION
    B.S. in Software Engineering
    University of Washington
    Graduated: 2018

    🏆 PROJECTS
    StreamScan – Real-time log aggregation system using Kafka and Spark

    EventGraph – Visual analytics tool built with Python Dash and PostgreSQL

    💬 CERTIFICATIONS
    Google Cloud Professional Data Engineer

"""

resume_3 = """

        JASON LEE
    📍 New York, NY | 📧 jason.lee@example.com | 📞 (917) 789-1234 | 💻 github.com/jasonlee | linkedin.com/in/jasonlee

    💼 PROFESSIONAL SUMMARY
    Creative Frontend Developer with 3+ years of experience building responsive web apps and e-commerce platforms. Strong focus on UI/UX design and performance optimization.

    🛠️ TECHNICAL SKILLS
    Languages: HTML5, CSS3, JavaScript (ES6+), TypeScript
    Frameworks/Libraries: React, Vue.js, TailwindCSS, Bootstrap
    Databases: Firebase, MongoDB
    Tools & Platforms: Netlify, Vercel, Git
    Testing: Jest, React Testing Library
    Other: Responsive Design, Figma, REST APIs, Agile

    👨‍💻 PROFESSIONAL EXPERIENCE
    Frontend Developer
    ShopEase | New York, NY
    January 2022 – Present

    Rebuilt the company’s storefront in React and TailwindCSS, improving mobile performance by 45%.

    Implemented a dynamic product search with Algolia API.

    Web Developer
    FreeLance Projects | Remote
    August 2019 – December 2021

    Delivered 15+ websites for small businesses, focusing on responsive design and SEO.

    🎓 EDUCATION
    B.A. in Graphic Design and Computer Science
    New York University (NYU)
    Graduated: 2019

    🏆 PROJECTS
    FoodMood – Recipe sharing app with React and Firebase

    📷 PhotoGrid – Portfolio site generator using Vue.js and Netlify

    💬 CERTIFICATIONS
    Meta Front-End Developer Professional Certificate

"""

resume_4 = """

        SOPHIA GARCIA
    📍 Miami, FL | 📧 sophia.garcia@example.com | 📞 (305) 456-7890 | 💻 github.com/sophiagarcia | linkedin.com/in/sophiagarcia

    💼 PROFESSIONAL SUMMARY
    DevOps Engineer with 5+ years of experience automating infrastructure, managing CI/CD pipelines, and ensuring system reliability for large-scale cloud environments.

    🛠️ TECHNICAL SKILLS
    Languages: Python, Bash, YAML
    Platforms/Tools: Kubernetes, Docker, Terraform, Ansible, Jenkins
    Cloud: AWS (EKS, ECS, S3, RDS), Azure
    Monitoring: Prometheus, Grafana, Datadog
    Other: Infrastructure as Code (IaC), Microservices, GitOps

    👨‍💻 PROFESSIONAL EXPERIENCE
    DevOps Engineer
    CloudSphere | Miami, FL
    April 2021 – Present

    Built Kubernetes clusters on AWS EKS and automated deployments using GitOps workflows.

    Developed Terraform modules for cloud infrastructure provisioning.

    Implemented centralized logging and monitoring using Prometheus and Grafana.

    Systems Engineer
    NetAxis Corp | Miami, FL
    July 2018 – March 2021

    Designed Ansible playbooks for system configuration across 100+ servers.

    🎓 EDUCATION
    B.S. in Information Technology
    Florida International University
    Graduated: 2018

    🏆 PROJECTS
    CloudGuard – Automated security scanning pipelines for cloud environments

    IaCify – Open-source CLI tool for automating IaC setup with Terraform

    💬 CERTIFICATIONS
    Certified Kubernetes Administrator (CKA)

    AWS Certified DevOps Engineer – Professional

"""

resume_5 = """

        OLIVER MARTINEZ
    📍 Denver, CO | 📧 oliver.martinez@example.com | 📞 (720) 654-3210 | 💻 github.com/olivermartinez | linkedin.com/in/olivermartinez

    💼 PROFESSIONAL SUMMARY
    Machine Learning Engineer with 3+ years of experience developing predictive models, natural language processing systems, and recommendation engines. Enthusiastic about applying ML to solve real-world business problems.

    🛠️ TECHNICAL SKILLS
    Languages: Python, R, SQL
    Libraries: TensorFlow, PyTorch, scikit-learn, SpaCy, NLTK
    Databases: PostgreSQL, BigQuery, MongoDB
    Tools & Platforms: AWS (SageMaker, S3, EC2), Docker
    Other: MLOps, Feature Engineering, Deep Learning, NLP

    👨‍💻 PROFESSIONAL EXPERIENCE
    Machine Learning Engineer
    InsightAI | Denver, CO
    October 2021 – Present

    Developed and deployed sentiment analysis models using BERT, achieving 88% accuracy.

    Built customer churn prediction models that reduced churn by 12%.

    Data Scientist
    DataCraft Labs | Remote
    September 2019 – September 2021

    Built recommendation engines for e-commerce clients using collaborative filtering.

    🎓 EDUCATION
    M.S. in Data Science
    University of Colorado Boulder
    Graduated: 2019

    🏆 PROJECTS
    NewsNLP – Automatic news article categorization using CNNs and BERT

    HealthPredict – Predictive health analytics dashboard built with Python Dash and AWS Lambda

    💬 CERTIFICATIONS
    TensorFlow Developer Certificate

    AWS Certified Machine Learning – Specialty

"""
resume_6 = """
Zhanna Qurs
Email: zhanna.qurs@example.com | Phone: (555) 123-4567 | GitHub: github.com/zhannaqurs | LinkedIn: linkedin.com/in/zhannaqurs

SUMMARY
--------
Detail-oriented and innovative Software Developer with 4+ years of experience in designing, building, and maintaining scalable web applications. Proficient in both frontend and backend development with a strong foundation in data structures, algorithms, and cloud technologies. Adept at problem-solving and working in fast-paced, agile environments.

SKILLS
-------
Languages: Python, JavaScript, TypeScript, SQL  
Frameworks: React, Node.js, Django, Express  
Tools & Platforms: Git, Docker, AWS, PostgreSQL, MongoDB  
Practices: REST APIs, Test-Driven Development, CI/CD, Agile Scrum

EXPERIENCE
-----------
Software Developer — TechNova Inc. (Remote)  
Jan 2022 – Present  
- Developed and maintained full-stack features for a SaaS analytics platform using React and Django.  
- Improved application performance by 30% by optimizing API queries and frontend rendering.  
- Led the migration from REST to GraphQL, reducing API call complexity by 40%.  

Junior Developer — BrightCode Solutions (Yerevan, Armenia)  
Aug 2019 – Dec 2021  
- Built reusable components and modular REST APIs for a job-matching platform.  
- Wrote unit and integration tests using Pytest and Jest, achieving 90% test coverage.  
- Participated in sprint planning and contributed to UI/UX improvements.

EDUCATION
----------
Bachelor of Science in Computer Science  
American University of Armenia, Yerevan  
Graduated: 2019

PROJECTS
---------
• **TaskTrackr** – A team productivity web app with real-time updates using WebSockets and React.  
• **DevMatch** – A developer matchmaking app using machine learning for skill-based pairing.  
• **Portfolio Website** – Personal portfolio built with Next.js, featuring interactive project showcases.

CERTIFICATIONS
---------------
• AWS Certified Developer – Associate (2023)  
• CS50: Introduction to Computer Science – HarvardX (2022)

"""

def read_single_pdf(pdf_path):
    reader = PdfReader(str(pdf_path))
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""  # Handle possible None
    return text.strip()

def read_pdfs_from_folder(folder_path):
    pdf_texts = {}

    # Make sure the path exists
    folder = Path(folder_path)
    if not folder.exists():
        raise FileNotFoundError(f"Folder {folder_path} does not exist.")

    # Loop through all PDF files
    for pdf_file in folder.glob('*.pdf'):
        reader = PdfReader(str(pdf_file))
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""  # Handle possible None
        pdf_texts = text.strip()

    return pdf_texts

import os.path

current_dir = os.path.dirname(os.path.abspath(__file__))

folder_path_jd = os.path.join(current_dir, "Resumes & JDs from client-20250413T193419Z-001", "Resumes & JDs from client", "Job descriptions", "Data Solutions Architect")

folder_path_cvs = os.path.join(current_dir, "Resumes & JDs from client-20250413T193419Z-001", "Resumes & JDs from client", "Resumes", "Data solution Architect")

weaviate_client = connect_to_local_weaviate()

import fitz

def extract_text_from_pdf(pdf_path):
    text = ""
    with fitz.open(pdf_path) as pdf:
        for page in pdf:
            text += page.get_text()
    return text

def UserAgreedOrNot(prompt, response):

    os.environ["AZURE_API_KEY"] = os.getenv("AZURE_OPENAI_KEY")
    os.environ["AZURE_API_BASE"] = os.getenv("AZURE_OPENAI_ENDPOINT")
    os.environ["AZURE_OPENAI_VERSION"]=os.getenv("AZURE_OPENAI_VERSION")

    llm = AzureChatOpenAI(
        deployment_name=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"), 
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_version=os.getenv("AZURE_OPENAI_VERSION"),
        api_key=os.getenv("AZURE_OPENAI_KEY"),
        temperature=0.7
    )

    llmResponse = llm.invoke("Say True or False if the user agrees: User response "+prompt+" to this question "+response)    

    return llmResponse.content



def job_description_information_checker(file_content, job_id):

        #print("💬 Welcome to the Product Database Assistant! (Type 'exit' to quit)\n") 

        #while True:
        global user_input

        response = job_description_writer(file_content)
        response = str(response)
        #print(response)   #This is the response from the job description writer agent

        # user_input = input("🧑 You: ")

        # if user_input.lower() in ['exit', 'quit']:
        #     print("👋 Goodbye!")
        #     #break

        # #boolValue = UserAgreedOrNot(user_input.lower(), str(response).lower())
        # #print(boolValue)
        # #if str(boolValue).lower()=="true":
        # if str(user_input).lower()=="yes":
        #     create_and_store_job_description(file_content,llm,weaviate_client)
        #     response = CV_scoring(job_id)   
        #     #break

        return response

class JDInput(BaseModel):
    folder_path_jd: str

class ResumeInput(BaseModel):
    folder_path_cvs: str
    job_id: str

class EmailResult(BaseModel):
    first_name: str
    last_name: str
    email: str

@app.post("/process-jd")
def process_job_description(data: JDInput):
    jd_data = read_pdfs_from_folder(data.folder_path_jd)
    response = router.route(jd_data)
    if response == 1:
        job_description_information_checker()
    return {"message": "Job description processed."}

@app.post("/analyze-resumes", response_model=List[EmailResult])
def analyze_resumes(data: ResumeInput):
    index = 0
    for filename in os.listdir(data.folder_path_cvs):
        full_path = os.path.join(data.folder_path_cvs, filename)
        content = extract_text_from_pdf(str(full_path))
        analyze_cv_resume(content, data.job_id, llm, weaviate_client)
        index += 1
        if index == 4:
            break

    engine = connect_to_postgres()
    Session = sessionmaker(bind=engine)
    session = Session()

    results = (
        session.query(Candidate.first_name, Candidate.last_name, Candidate.email)
        .join(Application)
        .filter(Application.overall_score > 80)
        .all()
    )

    email_list = []
    time_start = datetime.now() + timedelta(days=1, hours=1)

    for first_name, last_name, email in results:
        if email:
            email_body = f"""Dear {first_name} {last_name}, ..."""  # same as before
            send_email(email, "Interview Invitation - Data Solution Architect Role", email_body)
        email_list.append({"first_name": first_name, "last_name": last_name, "email": email})
        time_start += timedelta(days=1, hours=1)

    weaviate_client.close()
    return email_list


def CV_scoring(job_id):

        index = 0

        for filename in os.listdir(folder_path_cvs):

                full_path = os.path.join(folder_path_cvs, filename)

                content = extract_text_from_pdf(str(full_path))

                analyze_cv_resume(content, str(job_id),llm,weaviate_client)

                index+=1
                
                if index==4:
                    break

        engine = connect_to_postgres()
        Session = sessionmaker(bind=engine)
        session = Session()

        # Query to get candidate emails with overall_score > 80
        results = (
            session.query(Candidate.first_name, Candidate.last_name, Candidate.email, Application.job_title)
            .join(Application)
            .filter(Application.overall_score > 80)
            .filter(Application.job_title.isnot(None))
            .all()
        )

        # Query to get candidate emails with overall_score < 80
        results_ = (
            session.query(Candidate.first_name, Candidate.last_name, Candidate.email, Application.job_title)
            .join(Application)
            .filter(Application.overall_score < 80)
            .filter(Application.job_title.isnot(None))
            .all()
        )        

        #print(results)
        #emails = [email[0] for email in results if email[0]]   

        numberOfDays = 0

        time_start = datetime.now() + timedelta(days=1, hours=1)

        for first_name, last_name, email, role in results:
            
            email_body = f"""Dear {first_name} {last_name},

                We are pleased to invite you for an interview for the position of Data Solution Architecture at NexgAI company.

                Please find the details of your interview below:
                - Date: April 20, 2025
                - Time: {time_start} UKT
                - Platform: Google Meet
                - Meeting Link: [https://meet.google.com/obf-hjpw-ymm]

                Please ensure that you join the meeting on time. If you have any questions or need further assistance, feel free to reach out to us.
                
                From Company's Name"""

            send_email(email, "Interview Invitation - " + role + " Role", email_body)
            
            time_start += timedelta(days=(numberOfDays+1), hours=1)

            numberOfDays+=1

        for first_name, last_name, email, role in results_:
            
            email_body = f"""Dear {first_name} {last_name},

                We are pleased to invite you for an interview for the position of Data Solution Architecture at NexgAI company.

                Please find the details of your interview below:
                - Date: April 20, 2025
                - Time: {time_start} UKT
                - Platform: Google Meet
                - Meeting Link: [https://meet.google.com/obf-hjpw-ymm]

                Please ensure that you join the meeting on time. If you have any questions or need further assistance, feel free to reach out to us.
                
                From Company's Name"""

            send_email(email, "Interview Invitation - " + role + " Role", email_body)
            
            time_start += timedelta(days=(numberOfDays+1), hours=1)

            numberOfDays+=1            

        weaviate_client.close()    

@app.get("/job-descriptions", response_model=List[str])
def fetchAllTheJobDescription() -> List[str]:

    weaviate_client.connect()

    collection = weaviate_client.collections.get("JobDescription")

    # Fetch all objects (you can limit or filter as needed)
    object = collection.query.fetch_objects()

    # Extract object IDs (UUIDs)
    object_ids = [str(obj.uuid) for obj in object.objects]

    print(object_ids)

    return object_ids   
 
# Define the input model
class StarterProgramInput(BaseModel):
    query: str
    job_id: str 


@app.post("/starter-program")
def starter_program(payload: StarterProgramInput):

    #user_input = input("🧑 You: ")

    #user_input = read_pdfs_from_folder(folder_path_jd)

    # if user_input.lower() in ['exit', 'quit']:
    #     print("👋 Goodbye!")
    #     break

    user_input = payload.query
    job_id = payload.job_id

    response = router.route(user_input) 

    if response == 1:

       job_description_information_checker(user_input, job_id) 



    #create_and_store_job_description(read_pdfs_from_folder(folder_path_jd),llm,weaviate_client)
    #analyze_cv_resume(resume,"a91e4ac2-d339-464f-b0aa-d7eee0265682",llm,weaviate_client)

    #create_and_store_job_description(job_input,weaviate_client)

    else:

       return response


from fastapi import Form, UploadFile, File
from typing import Optional
 
@app.post('/company')
async def research_query( company_name: str = Form(None),
    job_title: str = Form(None),
    department: str = Form(None),
    responsibilities: str = Form(None),
    required_skills: str = Form(None),
    preferred_skills: str = Form(None),
    qualification: str = Form(None),
    experience: str = Form(None),
    employment_type: str = Form(None),
    location: str = Form(None),
    salary_range: str = Form(None),
    min_salary: str = Form(None),
    max_salary: str = Form(None),
    education_level: str = Form(None),
    job_description: str = Form(None),
    file: Optional[UploadFile] = File(None)):
 
    try:
        file_path = ""
        if file:
            file_path = f'jd/{file.filename}'
 
            with open(file_path, "wb") as doc:
                doc.write(file.file.read())
 
        company_details = {
            "title": job_title,
            "department" :department,
            "responsibilities": responsibilities,
            "required_skills": required_skills,
            "preferred_skills": preferred_skills,
            "qualification": [qualification],
            "experience": experience,
            "employment_type": employment_type,
            "location": location,
            "salary_range": salary_range,
            # min_salary,
            # max_salary,
            "experience":education_level,
            "job_description":job_description,
        }

        response = router.route(str(company_details))

        if response == 1: 
            response= await create_and_store_job_description(company_details,file_path,llm,weaviate_client)
            user_input = extract_text_from_pdf(str(file_path)) + str(company_details)
            response = job_description_information_checker(user_input, response['job_id']) 
            return {"status": 200, "response": response}
        
        else:

            return response
       
    except Exception as e:
        raise e
   
import uvicorn



if __name__ == "__main__":
    uvicorn.run("main:app", reload=True, host="0.0.0.0", port=8028)



# if __name__ == "__main__":
#    # router.route(resume_6)

#     # print("=============================JOB DESCRIPTION=============================")

#     # print(read_pdfs_from_folder(folder_path_jd))

#     # print("=============================JOB DESCRIPTION=============================")


#     #starter_program("6da57cff-058b-48bc-8748-dc840af0ba61")

#     #fetchAllTheJobDescription()

#     url = "http://localhost:8000/starter-program"  # API endpoint

#     data = {
#         "query": "Job Title: Solutions Architect I, Data Strategy\n Job Summary\n The Data Strategy organization at CCBSS collects, houses, and stewards a broad array of business, sales, and operational performance data. The Data Strategy and Development team specializes in building and supporting a broad suite of data functionality and capabilities including in-database logic, ETL, data management user interfaces, and custom business applications.\n We are looking for a candidate with strong data skills who can design and deploy new capabilities to enable data processes and reporting. In this role you will develop and leverage a deep understanding of the Coca-Cola business, its data systems and constraints, and the highly nuanced needs of its business teams and stakeholders.\n Duties and Responsibilities\n Leverage data modeling and software skills to design, build, test and document robust solutions\n Interpret stakeholder needs and translate into detailed, actionable work requirements\n Mary creative process improvement and business acumen to achieve elegant, sustainable solutions\n Steer business teams to successful adoption through training and change management\n Serve as subject matter expert, applying knowledge of business and data processes alike to identify opportunities and drive change autonomously\n Proactively identify risks, streamline interdependent efforts, and optimize the resources available to you\n Balance tactical execution with strategic thinking\n Key Skills and Abilities\n Ability to balance tactical execution with strategic thinking\n Passionate about data – can easily visualize complex data relationships and quickly learn new data tools\n Clear, concise, and personable communication to technical audiences and business leaders alike\n Logical, enthusiastic, and decisive approach to problem solving\n Works autonomously while remaining aligned to team and company goals\n Ability to quickly absorb and retain large amounts of information\n Helpful, positive approach to customer service\n Ability to influence stakeholders and project partners to achieve results\n Education Requirements\n Bachelor’s degree in engineering, statistics, business, or equivalent industry experience\n Years of Experience\n Minimum 5 years of experience in data, analytics, or IT\n Advanced skills in SQL required\n Experience building applications in Microsoft Power Platform preferred\n Experience building reporting capabilities using Azure suite (SQL DB, Synapse, SSIS, ADF, etc.) preferred\n Proficient in BI tools such as Tableau, PowerBI preferred\n Knowledge of Coke data systems highly preferred\n Required Travel\n Travel is not expected in this job, however, employees may be asked to travel for meetings or training on occasion.\n Hybrid Work Environment\n 1/2\n https://performancemanager4.successfactors.com/xi/ui/rcmcommon/pages/jobReqPrintPreview.xhtml?drawButtons=true&jobID=1687&isExternal=true…\n3/28/25, 9:29 AM\n Job Description Print Preview\n CCBSS operates a hybrid working environment. This is a teleworking role that requires working at a CCBSS office location on a regular basis (or a minimum number of days per month or week) at the manager’s discretion. The number of days required at a CCBSS office location is at the manager’s discretion and is subject to change depending on business needs.\n Company Message\n Coca-Cola Bottlers’ Sales and Services, LLC is an Equal Opportunity Employer and does not discriminate against any employee or applicant for employment because of race, color, sex, age, national origin, religion, sexual orientation, gender identity and/or expression, status as a veteran, and basis of disability or any other federal, state, or local protected class.",
#         "job_id": "6da57cff-058b-48bc-8748-dc840af0ba61"
#     }

#     response = requests.post(url, json=data)

#     # Print the response from the API
#     print(response.json())

#    # create_and_store_job_description(job_input,llm,weaviate_client)
#    # analyze_cv_resume(resume,"a91e4ac2-d339-464f-b0aa-d7eee0265682",llm,weaviate_client)
#     # folder_path = "Resumes/Data_solution_Architect"
#     # pdf_texts = read_pdfs_from_folder(folder_path)
#     # jd = read_pdfs_from_folder("Resumes/architech.pdf")
#     # count = 0
#     #     # Print all loaded resumes
#     # for filename, text in pdf_texts.items():
#     #     if count == 2:
#     #         break
#     #     print(f"--- {filename} ---\n{text}\n\n")
    
#     # li = [resume_1,resume_2,resume_3,resume_4,resume_5]
#     # for res in li:
#     # text = read_single_pdf("Resumes/Anush_Tadevosyan_Resume.pdf")
#     # print(text)

#     # analyze_cv_resume(text,"730b4e80-a88c-4bd7-8138-a48b65f6a0b6",llm,weaviate_client)
#     # #    # 411e6188-ace6-42b9-aa2a-0a094e690211
#     # # (text,jd,llm,weaviate_client)
    
    
#     # weaviate_client.close()