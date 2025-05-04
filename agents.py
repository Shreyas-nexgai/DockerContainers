import os
from datetime import datetime, timedelta
from langchain_openai import AzureChatOpenAI
#from tools import create_and_store_job_description,analyze_cv_resume
from crewai import Agent, Task, Crew, LLM, Process

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


# job_description_agent = Agent(
#     role="Job Description Specialist",
#     goal="Create detailed and effective job descriptions that accurately represent position requirements",
#     backstory="""You are an experienced HR professional with 15 years of experience writing job descriptions
#     across various industries. You have a talent for identifying key requirements and translating them into
#     clear, compelling job postings that attract qualified candidates.""",
#     verbose=True,
#     tools=[create_and_store_job_description],
#     allow_delegation=True,
#     llm=llm
# )

# Agent 1: Job Description Analyzer
jd_analyzer = Agent(
    role='Job Description Analyzer',
    goal='Thoroughly analyze the provided job description to identify key requirements, skills, experience levels, and company culture hints.',
    backstory=(
        "You are an expert HR analyst with a keen eye for detail. "
        "Your specialty is dissecting job descriptions to extract the most critical information "
        "needed for effective candidate screening. You understand technical jargon, soft skills, "
        "and the underlying needs of the hiring manager."
    ),
    verbose=True, # Enables detailed logging of the agent's execution
    allow_delegation=False, # This agent focuses solely on the JD
    #step_callback=reasoning_task,
    #task_callback=reasoning_task,
    #llm=llm,
    llm=LLM(model="azure/gpt-4o")
    # tools=[search_tool] # Optional: if JD analysis requires external context
)

# Task 1: Analyze the Job Description
# Note: The job_description variable will be passed in the inputs dictionary when running the crew.
task_analyze_jd = Task(
    description=(
        "Analyze the following Job Description text: '{job_description}'. "
        "Identify and list the key skills (technical and soft), required years of experience, "
        "educational requirements, and any other crucial qualifications mentioned. "
        "Present the analysis in a clear, structured format."
    ),
    expected_output=(
        "A structured summary of the core requirements extracted from the job description, "
        "including mandatory and preferred skills, experience level, education, etc."
    ),
    #step_callback=reasoning_task,
    agent=jd_analyzer,
)

# Agent 2: CV Parser & Information Extractor
cv_parser = Agent(
    role='CV Parser and Information Extractor',
    goal='Accurately parse candidate CVs (provided as text) to extract relevant information like contact details, work experience, skills, education, and projects.',
    backstory=(
        "You are a meticulous data extraction specialist. You can read through CVs in various formats (assuming text input) "
        "and systematically pull out structured information. You pay close attention to details like dates, job titles, "
        "skill keywords, and educational background."
    ),
    verbose=True,
    allow_delegation=False, # Focuses on parsing individual CVs
    #step_callback=reasoning_task_1,
    #task_callback=reasoning_task_1,
    #llm=llm,
    llm=LLM(model="azure/gpt-4o")
)

# Task 2: Parse a CV
# Note: This task will be dynamically created or adapted for each CV.
# The 'cv_content' will be passed in the inputs.
task_parse_cv = Task(
    description=(
        "Parse the following CV content: '{cv_content}'. "
        "Extract key information such as candidate name, contact info (optional), "
        "summary/objective, list of skills, work experience (job titles, companies, duration), "
        "and education background. Structure the extracted data clearly."
    ),
    expected_output=(
        "Structured data extracted from the CV, including sections for skills, "
        "work experience (with years calculated if possible), and education."
    ),
    #step_callback=reasoning_task,
    agent=cv_parser,
    # This task's output will be used by the assessment task.
    # We define context dynamically when running the loop.
)

# Agent 3: Candidate Assessor & Matcher
candidate_assessor = Agent(
    role='Candidate Assessor and Matcher',
    goal='Critically assess each candidate\'s extracted CV information against the key requirements derived from the job description. Provide a percentage score, suitability score and summary.',
    backstory=(
        "You are a seasoned recruitment specialist with experience matching candidates to roles. "
        "You take the structured information from a CV and the analyzed requirements from the JD "
        "to determine how well the candidate fits the role. You consider skills, experience years, "
        "education, and other relevant factors identified in the JD."
    ),
    verbose=True,
    allow_delegation=False, # Focuses on comparing one CV to the JD analysis
    #step_callback=reasoning_task_2,
    #task_callback=reasoning_task_2,
    #llm=llm,
    llm=LLM(model="azure/gpt-4o")
)

# Task 3: Assess a Candidate
# Note: This task needs context from both JD analysis and CV parsing.
task_assess_candidate = Task(
    description=(
        "Assess the candidate based on the parsed CV data against the job requirements analysis. "
        "Compare skills, years of experience, and education. "
        "Provide a summary of the match, highlighting strengths and weaknesses relative to the job description. "
        "Assign a suitability score (e.g., Poor Fit, Partial Match, Good Match, Excellent Match)."
    ),
    expected_output=(
        "A concise assessment report for the candidate, including a percentage score,suitability score,category "
        "and justification based on the comparison between the CV and job description requirements."
    ),
    #step_callback=reasoning_task,
    agent=candidate_assessor,
    context=[task_analyze_jd, task_parse_cv], # Depends on JD analysis and CV parsing
)

# Agent 4: Reporting Specialist
report_generator = Agent(
    role='Recruitment Reporting Specialist',
    goal='Compile the assessments of all candidates into a concise and informative report, ranking candidates based on the percentage score, suitability and highlighting key strengths or weaknesses.',
    backstory=(
        "You are an organized reporting expert. You synthesize information from multiple assessments "
        "to create clear, actionable reports for hiring managers. Your reports summarize the screening process, "
        "rank candidates, and provide justifications for the rankings."
    ),
    verbose=True,
    allow_delegation=False,
    #step_callback=reasoning_task(name="Recruitment Reporting Specialist"),
    #task_callback=reasoning_task(name="Recruitment Reporting Specialist"),
    #step_callback=reasoning_task_3,
    #task_callback=reasoning_task_3,
    #llm=llm,
    llm=LLM(model="azure/gpt-4o")
)

task_compile_report = Task(
    description=(
        "Compile a final screening report based on the assessments of all processed candidates. "
        "The report should list the candidates, their percentage score,suitability score,category, and a brief summary of why. "
        "Rank the candidates from most to least suitable based on the assessments."
        "Input assessments will be provided as context." # This is handled by passing results in the loop
    ),
    # expected_output=(
    #     "A comprehensive report summarizing the screening results, ranking candidates, "
    #     "and providing brief justifications for each candidate's assessment."
    # ),
    expected_output=(
        '''
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
        '''
    ),
    #step_callback=reasoning_task,
    agent=report_generator,
    # Context will be the list of assessment results, added dynamically.
)

assessment_result = ""

# --- Function to Run the Screening Process ---

def screen_cvs(job_description, cv_contents_list):
    """
    Runs the CrewAI screening process for a list of CVs against a job description.

    Args:
        job_description (str): The full text of the job description.
        cv_contents_list (list[str]): A list where each element is the text content of a CV.

    Returns:
        str: The final report generated by the reporting agent.
    """
    all_assessment_results = []
    num_cvs = len(cv_contents_list)

    print(f"Starting screening process for {num_cvs} CV(s)...")

    # --- Step 1: Analyze the Job Description (Run once) ---
    jd_crew = Crew(
        agents=[jd_analyzer],
        tasks=[task_analyze_jd],
        process=Process.sequential,
        #step_callback=reasoning_task,
        verbose=True
    )
    print("\n--- Analyzing Job Description ---")
    jd_analysis_result = jd_crew.kickoff(inputs={'job_description': job_description})
    print("\n--- Job Description Analysis Complete ---")
    print(jd_analysis_result) # Log the JD analysis output

    # --- Step 2 & 3: Parse CV and Assess Candidate (Loop through CVs) ---
    for i, cv_content in enumerate(cv_contents_list):
        print(f"\n--- Processing CV {i+1}/{num_cvs} ---")

        # Create a crew for parsing and assessing *this specific* CV
        # Pass the JD analysis result implicitly via task context
        screening_crew = Crew(
            agents=[cv_parser, candidate_assessor],
            #step_callback=reasoning_task,
            # IMPORTANT: Ensure tasks use the correct context.
            # task_analyze_jd provides JD context to task_assess_candidate.
            # task_parse_cv provides CV context to task_assess_candidate.
            tasks=[task_parse_cv, task_assess_candidate],
            process=Process.sequential,
            verbose=True
        )

        global full_name

        full_name = " ".join(cv_content.split()[:2])

        global assessment_result

        # Run the crew for this CV
        assessment_result = screening_crew.kickoff(inputs={
            'cv_content': cv_content,
            # JD analysis context is implicitly passed via task definition
            # We could optionally make jd_analysis_result an explicit input if needed
        })

        print(f"\n--- Assessment Complete for CV {i+1} ---")
        print(assessment_result) # Log the assessment output
        all_assessment_results.append(f"Candidate {i+1} Assessment:\n{assessment_result}")

    print("\n--- Final Report Generated ---")
    return all_assessment_results

def job_description_writer(input):

    # Required fields
    required_info = [
        "job title",
        "department",
        "employment type",
        "location",
        "required years of experience",
        "education level"
    ]

    job_description_agent = Agent(
        role="Job Description Specialist",
        goal="Create detailed and effective job descriptions that accurately represent position requirements",
        backstory="""You are an experienced HR professional with 15 years of experience writing job descriptions
        across various industries. You have a talent for identifying key requirements and translating them into
        clear, compelling job postings that attract qualified candidates.""",
        verbose=True,
        #tools=[create_and_store_job_description],
        allow_delegation=True,
        llm=LLM(model="azure/gpt-4o")
    )

    # Agent 2: Verifier
    verifier_agent = Agent(
        role="VerifierAgent",
        goal=f"""Analyze the job description text: {input} to verify all required elements are present. REMEMBER IF THERE ARE NO MISSING JOB DESCRIPTION DETAILS ASK THE USER TO CONFIRM THAT THEY ARE HAPPY TO SAVE IT.""",
        backstory="You're an expert in HR compliance, ensuring job descriptions are complete and professional.",
        verbose=True,
        allow_delegation=True,
        llm=LLM(model="azure/gpt-4o")
    )

    verifier_agent_tasks = Task(
        description=f"""Verify all required job description details: {required_info} are present in this job description: {input}.""",
        agent=verifier_agent,
        expected_output="List of missing details",
    )

    # Agent 3: Communicator
    communicator_agent = Agent(
        role="CommunicatorAgent",
        goal=f"""Inform the user of any missing fields or confirm that the job description: {input} is complete. REMEMBER IF THERE ARE NO MISSING JOB DESCRIPTION DETAILS ASK THE USER TO CONFIRM THAT THEY ARE HAPPY TO SAVE IT.""",
        backstory="You're a helpful assistant who communicates whether any information is missing from the job description.",
        verbose=True,
        allow_delegation=True,
        llm=LLM(model="azure/gpt-4o")
    )

    communicator_agent_tasks = Task(
        description=f"""Inform the user about any missing or complete job description details: {required_info}.""",
        agent=communicator_agent,
        expected_output="Message to user",
    )

    job_description_task = Task(
        description=str(input),
        agent=job_description_agent,
        expected_output="A complete job description with all sections well formatted and then confirm it with the user if they are happy to upload it. REMEMBER THIS AS WELL",
    )

    crew = Crew(
    agents=[job_description_agent, verifier_agent, communicator_agent],
    tasks=[job_description_task, verifier_agent_tasks, communicator_agent_tasks],
    process=Process.sequential  # You can change this to parallel if multiple agents
    )

    result = crew.kickoff()
    return result

# cv_analysis_agent = Agent(
#     role="Resume Analyzer",
#     goal="Thoroughly analyze resumes against job requirements to identify the best candidates",
#     backstory="""You are an expert in talent acquisition with a background in both technical and non-technical roles.
#     You can quickly identify how a candidate's experience, skills, and qualifications align with job requirements.
#     You have a keen eye for spotting both explicit and implicit qualifications in resumes.""",
#     verbose=True,
#     allow_delegation=False,
#     tools = [analyze_cv_resume],
#     llm=llm
# )
