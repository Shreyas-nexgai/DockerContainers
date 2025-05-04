import weaviate
import weaviate.classes as wvc


def connect_to_local_weaviate() -> weaviate.WeaviateClient:
 
    print("Connecting to local Weaviate...")
    client = weaviate.connect_to_local(host="localhost", port="8080", grpc_port="50051")
    return client

def create_job_description_collection(client: weaviate.WeaviateClient):
  
    collection_name = "JobDescription"
    properties = [
        wvc.config.Property(name="title", data_type=wvc.config.DataType.TEXT, description="The title of the job position"),
        wvc.config.Property(name="department", data_type=wvc.config.DataType.TEXT, description="Department or team where the position belongs"),
        wvc.config.Property(
            name="fullDescription",
            data_type=wvc.config.DataType.TEXT,
            description="Complete job description text",
        ),
        wvc.config.Property(name="responsibilities", data_type=wvc.config.DataType.TEXT_ARRAY, description="Key responsibilities of the role"),
        wvc.config.Property(name="requiredSkills", data_type=wvc.config.DataType.TEXT_ARRAY, description="List of required skills for the position"),
        wvc.config.Property(name="preferredSkills", data_type=wvc.config.DataType.TEXT_ARRAY, description="List of preferred or nice-to-have skills"),
        wvc.config.Property(name="minimumQualifications", data_type=wvc.config.DataType.TEXT_ARRAY, description="Minimum education and experience requirements"),
        wvc.config.Property(name="experienceYears", data_type=wvc.config.DataType.TEXT, description="Required years of experience"),
        wvc.config.Property(name="employmentType", data_type=wvc.config.DataType.TEXT, description="Type of employment (Full-time, Part-time, Contract, etc.)"),
        wvc.config.Property(name="location", data_type=wvc.config.DataType.TEXT, description="Job location or remote status"),
        wvc.config.Property(name="salaryRange", data_type=wvc.config.DataType.TEXT, description="Salary range for the position"),
        wvc.config.Property(name="createdAt", data_type=wvc.config.DataType.DATE, description="When the job description was created"),
        wvc.config.Property(name="updatedAt", data_type=wvc.config.DataType.DATE, description="When the job description was last updated"),
        wvc.config.Property(name="jobId", data_type=wvc.config.DataType.TEXT, description="Reference ID to the SQL job table")
    ]

    vectorizer_config = wvc.config.Configure.Vectorizer.none()


    client.collections.create(
        name=collection_name,
        description="Schema for storing job descriptions and related metadata",
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
            create_job_description_collection(client)
        else:
            print("Weaviate client could not connect.")

        client.close()

    except Exception as e:
        print(f"An unexpected error occurred during connection or schema creation: {e}")
    finally:
        if client and client.is_connected():
             client.close()
             print("Weaviate client connection closed.")