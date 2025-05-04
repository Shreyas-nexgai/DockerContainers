from weaviate import Client

def fetch_jd_text_and_title(jd_id,weaviate_client):
    collection = weaviate_client.collections.get("JobDescription")
    jd_object = collection.query.fetch_object_by_id(jd_id)

    if jd_object is None:
        print(f"[ERROR] JobDescription with ID {jd_id} not found.")
        return None, None

    jd_text = ""
    for field, value in jd_object.properties.items():
        jd_text += str(field) + " - " + str(value) + "\n"

    return jd_text, jd_object.properties["title"]

def store_detailed_resume_analysis(analysis_object,weaviate_client):
    collection = weaviate_client.collections.get("ResumeAnalysis")
    uuid = collection.data.insert(analysis_object)
    return uuid