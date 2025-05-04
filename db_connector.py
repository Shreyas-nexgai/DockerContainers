from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

def get_db_uri():
    username = "postgres"
    password = "marviniscool"
    host = "localhost"
    port = "5432"
    database = "hr_system"

    connection_url = f"postgresql+psycopg2://{username}:{password}@{host}:{port}/{database}"
    return connection_url

def get_db_engine():
    connection_url = get_db_uri()
    engine = create_engine(connection_url)
    return engine

def check_connection():
    engine = get_db_engine()
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT * FROM jobs LIMIT 1;"))  # test any table you have
            print("Connection successful:", result.fetchone())
    except Exception as e:
        print("Connection failed:", e)

def check_connection_session():
    engine = get_db_engine()
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        with session.begin():
            result = session.execute(text("SELECT * FROM jobs LIMIT 5;"))
            print("Connection successful via session:", result.fetchall())
    except Exception as e:
        print("Connection failed via session:", e)
    finally:
        session.close()

if __name__ == "__main__":
    check_connection()
    check_connection_session()
