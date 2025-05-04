from typing import Any, Type, Union
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

class NL2SQLToolInput(BaseModel):
    sql_query: str = Field(
        title="SQL Query",
        description="The SQL query to execute.",
        alias="query"
    )

    class Config:
        allow_population_by_alias = True

class NL2SQLTool(BaseTool):
    name: str = "NL2SQL Tool"
    description: str = "Executes SQL queries on the connected PostgreSQL database."
    db_uri: str = Field(
        title="Database URI",
        description="Use the format postgresql+psycopg2://user:password@host:port/database"
    )
    tables: list = []
    columns: dict = {}
    table_data: dict = {}
    flag: bool = False
    top: int = 10
    args_schema: Type[BaseModel] = NL2SQLToolInput

    def model_post_init(self, __context: Any) -> None:
        self._initialize_metadata()

    def _initialize_metadata(self):
        data = {}
        table_data = {}
        tables = self._fetch_available_tables() if not self.tables else self.tables

        if not self.columns:
            for table in tables:
                table_name = table.get("table_name")
                if table_name:
                    table_columns = self._fetch_all_available_columns(table_name)
                    data[f'{table_name}_columns'] = table_columns
                    if self.flag:
                        table_data[f'{table_name}_data'] = self._fetch_table_data(self.top, table_name)

            self.tables = tables
            self.columns = data
            self.table_data = table_data

    def _fetch_available_tables(self):
        return self.execute_sql(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';"
        )

    def _fetch_all_available_columns(self, table_name: str):
        return self.execute_sql(
            f"""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_schema = 'public' 
            AND table_name = '{table_name}';
            """
        )

    def _fetch_table_data(self, top: int, table_name: str):
        print(f"Fetching top {top} rows from {table_name}...")
        return self.execute_sql(
            f"SELECT * FROM {table_name} LIMIT {top};"
        )

    def _run(self, sql_query: str):
        try:
            data = self.execute_sql(sql_query)
        except Exception as exc:
            print("SQL Execution Error:", exc)
            data = (
                f"Could not execute query: {sql_query}. "
                f"Available tables: {self.tables}. Columns: {self.columns}. Error: {exc}"
            )
        return data

    def execute_sql(self, sql_query: str) -> Union[list, str]:
        engine = create_engine(self.db_uri)
        Session = sessionmaker(bind=engine)
        session = Session()

        try:
            with session.begin():
                result = session.execute(text(sql_query))
                if result.returns_rows:
                    rows = result.fetchall()
                    columns = result.keys()
                    return [dict(zip(columns, row)) for row in rows]
                else:
                    return f"Query executed successfully: {sql_query}"
        except SQLAlchemyError as e:
            print("Database error:", e)
            session.rollback()
            raise e
        finally:
            session.close()
