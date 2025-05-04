from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, Text, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime, timezone

def connect_to_postgres():
    username = "postgres"
    password = "marviniscool"  
    host = "localhost"         
    port = "5432"              
    database = "hr_system"     

    connection_string = f"postgresql://{username}:{password}@{host}:{port}/{database}"
    engine = create_engine(connection_string)
    return engine

Base = declarative_base()

class Job(Base):
    __tablename__ = 'jobs'

    id = Column(String(255), primary_key=True)
    title = Column(String(1000))
    department = Column(String(1000))
    weaviate_description_id = Column(String(255))
    employment_type = Column(String(50))
    location = Column(String(1000))
    # salary_min = Column(Integer, default=0)
    # salary_max = Column(Integer, default=100000)
    required_experience_years = Column(Integer)
    education_level = Column(String(1000))
    status = Column(String(50))
    rounds_total = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))
    

   # applications = relationship("Application", back_populates="job")


class Candidate(Base):
    __tablename__ = 'candidates'
    
    id = Column(Integer, primary_key=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255))
    phone = Column(String(50))
    resume_path = Column(String(255))  # File path or URL to resume
    linkedin_url = Column(String(255))
    github_url = Column(String(255))
    portfolio_url = Column(String(255))
    current_position = Column(String(225))
    current_company = Column(String(225))
    location = Column(String(100))
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))
    

    applications = relationship("Application", back_populates="candidate")


class Application(Base):
    __tablename__ = 'applications'
    
    id = Column(Integer, primary_key=True)
    candidate_id = Column(Integer, ForeignKey('candidates.id'), nullable=False)
    job_id = Column(String(255))  # Changed to String to match Job.id
    job_title = Column(String(255))
    status = Column(String(50))  # Applied, Screening, Interview, Rejected, Hired
    overall_score = Column(Float)  # 0-100 fit score
    technical_score = Column(Float)
    experience_score = Column(Float)
    education_score = Column(Float)
    current_round = Column(Integer, default=0)  # Current interview round (0 = not yet in interview stage)
    weaviate_analysis_id = Column(String(255))  # Reference to Weaviate ResumeAnalysis
    rejection_reason = Column(Text)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))
    

    candidate = relationship("Candidate", back_populates="applications")
    #job = relationship("Job", back_populates="applications")


if __name__ == "__main__":
    engine = connect_to_postgres()
    Base.metadata.create_all(engine)
    print("Tables created successfully.")


# Interviews, Email Template table


