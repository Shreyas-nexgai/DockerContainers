import os
from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI
from crewai import Agent, Task, Crew
from crewai.agents.parser import AgentAction
from database_engine_tool import NL2SQLTool
from db_connector import get_db_uri

# Load environment variables
load_dotenv()

os.environ["AZURE_API_KEY"] = os.getenv("AZURE_OPENAI_KEY")
os.environ["AZURE_API_BASE"] = os.getenv("AZURE_OPENAI_ENDPOINT")
os.environ["AZURE_API_VERSION"] = os.getenv("AZURE_OPENAI_VERSION")

# Azure OpenAI LLM setup
llm = AzureChatOpenAI(
    azure_deployment="azure/" + os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_version=os.getenv("AZURE_API_VERSION"),
    api_key=os.getenv("AZURE_OPENAI_KEY"),
    temperature=0.7
)

# Setup NL2SQL tool for Postgres
nl2sql_tool = NL2SQLTool(
    db_uri=str(get_db_uri()),  # <- from db_connector
    tables=[],  # let it auto-fetch tables
    columns={}, # let it auto-fetch columns
    flag=True,  # optional: also fetch top rows as sample
    top=5
)

class SQLAgent:
    def __init__(self):
        self.sql_agent = Agent(
            role="Postgres Resume SQL Analyst",
            goal="Generate and execute SQL queries against the HR system database (candidates, applications, jobs).",
            backstory="""An expert SQL analyst specialized in analyzing candidate profiles, job postings, and applications 
            using SQL queries in a PostgreSQL database. Skilled at retrieving structured data based on user questions.""",
            tools=[nl2sql_tool],
            verbose=True,
            allow_delegation=False,
            step_callback=self.step_callback,
            llm=llm
        )

    def step_callback(self, step):
        if isinstance(step, AgentAction):
            print(f"Agent step: {step.text.replace('```','')}")
            
    def create_query_task(self, tables, columns, question):
        column_description = "\n".join([f"- {k}: {v}" for k, v in columns.items()])

        query_task = Task(
            description=(
                f"Given these tables {tables} and their columns:\n{column_description}\n\n"
                f"Generate a PostgreSQL SQL query to answer the question: \"{question}\".\n"
                "Use 'LIMIT' instead of 'TOP'.\n"
                "Avoid using square brackets [].\n"
                "Respond only with the final query result (do not show the query itself).\n"
                "Format your answer using clean HTML tags where needed (e.g., <p>, <ul>, <li>)."
            ),
            expected_output="Final result only, cleanly structured in HTML if needed.",
            agent=self.sql_agent
        )
        return query_task

    def ask_question(self, question):
        try:
            tables = nl2sql_tool.tables
            columns = nl2sql_tool.columns
            query_task = self.create_query_task(tables, columns, question)

            crew = Crew(
                agents=[self.sql_agent],
                tasks=[query_task]
            )
            result = crew.kickoff()
            return result
        except Exception as e:
            print("Error during SQL Agent task:", e)
            return None

if __name__ == "__main__":
    sql_agent = SQLAgent()
    question = "How many rows are there in the Applications table?."
    final_answer = sql_agent.ask_question(question)
    print("Final Answer:", final_answer)
