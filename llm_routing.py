from agents import llm
from schemas.jobDescriptions_wv import connect_to_local_weaviate
from tools import create_and_store_job_description, analyze_cv_resume_given_jd, analyze_cv_resume

class LLMRouter:
    def __init__(self, llm):
        self.llm = llm
        self.weaviate_client = connect_to_local_weaviate()

    def determine_function(self, user_input: str):
        routing_prompt = f"""
        You are an intent classifier. Given the user input below, determine the intent.

        - If the user input contains a job description or appears to describe a role, position, responsibilities, or hiring needs, return the number **1**.
        - If the user input contains a resume, candidate background, professional summary, or any mention of a person’s work history, skills, or contact details, return the number **2**.

        Respond only with **1** or **2** — no additional text.

        User Input:
        {user_input}
        """

        response = self.llm.invoke(routing_prompt).content.strip()
        return int(response)
    
    def route(self,user_input):
        response = self.determine_function(user_input)
        print(f"response is {response}, type is {type(response)}")

        if response == 1:
            #create_and_store_job_description(user_input,self.llm,self.weaviate_client)
            #job_description_information_checker()
            return response
        elif response == 2:
            #analyze_cv_resume(user_input,"730b4e80-a88c-4bd7-8138-a48b65f6a0b6",self.llm,self.weaviate_client)
            return response


router = LLMRouter(llm)
