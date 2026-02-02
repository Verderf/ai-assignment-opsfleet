from src.state import AgentState
from src.utils.bigquery_runner import BigQueryRunner
import os
import logging

class SQLExecutor:
    def __init__(self):
        logging.basicConfig(level=logging.INFO)
        self.runner = None
        try:
            project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
            self.runner = BigQueryRunner(project_id=project_id)
            logging.info("SQLExecutor initialized with real BigQuery connection.")
        except Exception as e:
            logging.error(f"Failed to initialize BigQuery runner: {str(e)}")
            logging.error("Ensure GOOGLE_APPLICATION_CREDENTIALS and GOOGLE_CLOUD_PROJECT are set in .env")

    def run(self, state: AgentState) -> dict:
        sql = state.get("generated_sql")
        if not sql:
            return {"error": "No SQL query generated.", "retry_count": state.get("retry_count", 0) + 1}
        
        if not self.runner:
            return {"error": "BigQuery runner not initialized. Check credentials and project ID.", "retry_count": state.get("retry_count", 0) + 1}
        
        try:
            logging.info(f"\n[Executing SQL]...")
            df = self.runner.execute_query(sql)
            # Convert DataFrame to list of dicts
            data = df.to_dict(orient='records')
            logging.info(f"Query returned {len(data)} rows")
            return {"query_result": data, "error": None}
        except Exception as e:
            logging.error(f"Query execution failed: {str(e)}")
            return {"error": str(e), "retry_count": state.get("retry_count", 0) + 1}

def sql_executor_node(state: AgentState):
    executor = SQLExecutor()
    return executor.run(state)
