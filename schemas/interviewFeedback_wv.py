import weaviate
# Use weaviate.classes.config for precise type hints for config objects
import weaviate.classes.config as wvc
#from weaviate.exceptions import WeaviateException # Import exceptions
from weaviate.exceptions import WeaviateQueryException

# Use connect_to_local for a standard local Weaviate instance (e.g., in Docker)
def connect_to_local_weaviate() -> weaviate.WeaviateClient:
    """
    Connects to a local Weaviate instance using the v4 client.
    Assumes Weaviate is running on localhost with default HTTP/gRPC ports.
    Adjust host/ports if necessary based on your Docker mapping.
    """
    print("Connecting to local Weaviate...")
    # Default ports for connect_to_local are http_port=8080, grpc_port=50051
    # If your Docker maps differently, use connect_to_custom:
    # client = weaviate.connect_to_custom(http_host="localhost", http_port="9000", grpc_port="50051")
    # If you need API key for OpenAI:
    # client = weaviate.connect_to_local(
    #     headers={
    #         "X-OpenAI-Api-Key": "YOUR_OPENAI_API_KEY"
    #     }
    # )
    client = weaviate.connect_to_local()
    return client

def create_interview_feedback_collection_v4(client: weaviate.WeaviateClient):
    """
    Creates the InterviewFeedback collection (schema) in Weaviate using the v4 client.
    Configures text2vec-openai as the vectorizer for the collection.
    """
    collection_name = "InterviewFeedback"

    # Define collection-level vectorizer config using wvc.config.Configure.Vectorizer
    # This applies text2vec-openai to the entire collection
    vectorizer_config = wvc.config.Configure.Vectorizer.text2vec_openai(
        model="ada",
        model_version="002",
        vectorize_collection_name=False # Typically set to False
    )

    # Define properties using a list of wvc.config.Property objects
    # Data types use wvc.config.DataType enums or strings ('text', 'text[]', etc.)
    properties = [
        wvc.config.Property(name="candidateId", data_type=wvc.config.DataType.TEXT, description="Reference ID to the SQL candidate table"),
        wvc.config.Property(name="jobId", data_type=wvc.config.DataType.TEXT, description="Reference ID to the SQL job table"),
        wvc.config.Property(name="applicationId", data_type=wvc.config.DataType.TEXT, description="Reference ID to the SQL application table"),
        wvc.config.Property(name="interviewId", data_type=wvc.config.DataType.TEXT, description="Reference ID to the SQL interview table"),
        wvc.config.Property(name="roundNumber", data_type=wvc.config.DataType.NUMBER, description="Interview round number"),
        wvc.config.Property(name="interviewType", data_type=wvc.config.DataType.TEXT, description="Type of interview (Technical, Behavioral, HR, etc.)"),
        wvc.config.Property(name="interviewDate", data_type=wvc.config.DataType.DATE, description="When the interview took place"),
        wvc.config.Property(
            name="overallFeedback",
            data_type=wvc.config.DataType.TEXT,
            description="Complete interview feedback and assessment",
            # Explicitly configure this property's contribution to the vector (matching v3 moduleConfig)
            module_config=wvc.config.Configure.Property.text2vec_openai(
                 skip=False, # Ensure this property is NOT skipped
                 vectorize_property_name=False # Parameter name in v4
            )
        ),
        wvc.config.Property(name="technicalAssessment", data_type=wvc.config.DataType.TEXT, description="Detailed assessment of technical skills"),
        wvc.config.Property(name="behavioralAssessment", data_type=wvc.config.DataType.TEXT, description="Assessment of behavioral and soft skills"),
        wvc.config.Property(name="questionsAndAnswers", data_type=wvc.config.DataType.TEXT_ARRAY, description="List of questions asked and answers provided"),
        wvc.config.Property(name="keyStrengths", data_type=wvc.config.DataType.TEXT_ARRAY, description="Key strengths demonstrated during the interview"),
        wvc.config.Property(name="areasForImprovement", data_type=wvc.config.DataType.TEXT_ARRAY, description="Areas where the candidate could improve"),
        wvc.config.Property(name="technicalScore", data_type=wvc.config.DataType.NUMBER, description="Numeric assessment of technical performance (0-100)"),
        wvc.config.Property(name="communicationScore", data_type=wvc.config.DataType.NUMBER, description="Numeric assessment of communication skills (0-100)"),
        wvc.config.Property(name="cultureFitScore", data_type=wvc.config.DataType.NUMBER, description="Numeric assessment of cultural fit (0-100)"),
        wvc.config.Property(name="recommendationLevel", data_type=wvc.config.DataType.TEXT, description="Recommendation level for this round (Strong Yes, Yes, Maybe, No, Strong No)"),
        wvc.config.Property(name="nextSteps", data_type=wvc.config.DataType.TEXT, description="Recommended next steps for this candidate"),
        wvc.config.Property(name="followUpQuestions", data_type=wvc.config.DataType.TEXT_ARRAY, description="Suggested follow-up questions for next rounds"),
        wvc.config.Property(name="interviewerNotes", data_type=wvc.config.DataType.TEXT, description="Additional notes from the interviewer"),
        wvc.config.Property(name="candidateQuestions", data_type=wvc.config.DataType.TEXT_ARRAY, description="Questions asked by the candidate"),
        wvc.config.Property(name="candidateResponseQuality", data_type=wvc.config.DataType.TEXT, description="Assessment of the quality of candidate's responses")
    ]

    # Check if collection exists by attempting to get it (v4 standard way)
    try:
        client.collections.get(collection_name)
        print(f"Collection '{collection_name}' already exists.")
    except WeaviateQueryException: # Catch the exception if the collection does not exist
         try:
            # Create the collection using client.collections.create
            client.collections.create(
                name=collection_name,
                description="Schema for storing interview feedback and assessments",
                properties=properties,
                vectorizer_config=vectorizer_config, # Apply the text2vec-openai vectorizer
                # module_config is typically not needed at the collection level
                # unless configuring global module settings beyond the vectorizer
            )
            print(f"Collection '{collection_name}' created successfully.")
         except WeaviateQueryException as e:
            print(f"Error creating collection '{collection_name}': {e}")


if __name__ == "__main__":
    client = None # Initialize client variable
    try:
        # Connect to Weaviate
        client = connect_to_local_weaviate()

        # Check if the client is successfully connected (optional but good practice)
        if client.is_connected():
            print("Weaviate client connected.")
            # Create the schema (collection)
            create_interview_feedback_collection_v4(client)
        else:
            print("Weaviate client could not connect.")

        client.close()

    except Exception as e:
        print(f"An unexpected error occurred during connection or schema creation: {e}")
    finally:
        # Ensure the client connection is closed
        if client and client.is_connected():
             client.close()
             print("Weaviate client connection closed.")