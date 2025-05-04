import weaviate
import weaviate.classes as wvc

def connect_to_local_weaviate() -> weaviate.WeaviateClient:
 
    print("Connecting to local Weaviate...")
    client = weaviate.connect_to_local(host="localhost", port="8080", grpc_port="50051")
    return client

def create_resume_analysis_collection_v4(client: weaviate.WeaviateClient):

    collection_name = "ResumeAnalysis"

    properties = [
        wvc.config.Property(name="candidateId", data_type=wvc.config.DataType.TEXT, description="Reference ID to the SQL candidate table"),
        wvc.config.Property(name="jobId", data_type=wvc.config.DataType.TEXT, description="Reference ID to the SQL job table"),
        wvc.config.Property(name="applicationId", data_type=wvc.config.DataType.TEXT, description="Reference ID to the SQL application table"),
        wvc.config.Property(
            name="overallAssessment",
            data_type=wvc.config.DataType.TEXT,
            description="Complete analysis and reasoning about the candidate"
        ),
        wvc.config.Property(name="skillMatchAnalysis", data_type=wvc.config.DataType.TEXT, description="Detailed analysis of how candidate skills match job requirements"),
        wvc.config.Property(name="experienceRelevance", data_type=wvc.config.DataType.TEXT, description="Analysis of relevance of candidate's experience to the position"),
        wvc.config.Property(name="educationFitAnalysis", data_type=wvc.config.DataType.TEXT, description="Reasoning about candidate's educational background"),
        wvc.config.Property(name="strengths", data_type=wvc.config.DataType.TEXT_ARRAY, description="Key strengths identified in the candidate's profile"),
        wvc.config.Property(name="weaknesses", data_type=wvc.config.DataType.TEXT_ARRAY, description="Areas where the candidate may not meet requirements"),
        wvc.config.Property(name="skillGaps", data_type=wvc.config.DataType.TEXT_ARRAY, description="Specific skills required by the job that the candidate lacks"),
        wvc.config.Property(name="recommendedQuestions", data_type=wvc.config.DataType.TEXT_ARRAY, description="Suggested interview questions based on resume analysis"),
        wvc.config.Property(name="fitScore", data_type=wvc.config.DataType.NUMBER, description="Numeric assessment of candidate fit (0-100)"),
        wvc.config.Property(name="technicalScore", data_type=wvc.config.DataType.NUMBER, description="Numeric assessment of technical skills (0-100)"),
        wvc.config.Property(name="experienceScore", data_type=wvc.config.DataType.NUMBER, description="Numeric assessment of relevant experience (0-100)"),
        wvc.config.Property(name="potentialFlags", data_type=wvc.config.DataType.TEXT_ARRAY, description="Potential concerns or areas needing follow-up"),
        wvc.config.Property(name="matchedSkills", data_type=wvc.config.DataType.TEXT_ARRAY, description="List of skills that match job requirements"),
        wvc.config.Property(name="recommendationLevel", data_type=wvc.config.DataType.TEXT, description="Recommendation level (Strong Yes, Yes, Maybe, No, Strong No)"), # string in v3 maps to TEXT in v4
        wvc.config.Property(name="analysisDate", data_type=wvc.config.DataType.DATE, description="When the analysis was performed")
    ]
    vectorizer_config = wvc.config.Configure.Vectorizer.none()

    client.collections.create(
        name=collection_name,
        description="Schema for storing detailed resume analysis and reasoning",
        properties=properties,
        vectorizer_config=vectorizer_config,
    )
    print(f"Collection '{collection_name}' created successfully.")


if __name__ == "__main__":
    client = None 
    try:
        client = connect_to_local_weaviate()

        if client.is_connected():
            print("Weaviate client connected.")
            create_resume_analysis_collection_v4(client)
        else:
            print("Weaviate client could not connect.")

        client.close()    

    except Exception as e:
        print(f"An unexpected error occurred during connection or schema creation: {e}")
    finally:
        if client and client.is_connected():
             client.close()
             print("Weaviate client connection closed.")