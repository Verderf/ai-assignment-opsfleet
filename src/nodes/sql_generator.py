from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from src.state import AgentState
from src.utils.golden_knowledge import GoldenKnowledgeBase
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SQLGenerator:
    def __init__(self):
        model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
        api_key = os.getenv("GOOGLE_API_KEY")
        logger.info(f"Using Gemini model: {model_name}")
        if not api_key:
            logger.error("GOOGLE_API_KEY is not set!")
        
        self.llm = ChatGoogleGenerativeAI(
            model=model_name, 
            google_api_key=api_key,
            temperature=0
        )
        self.golden_kb = GoldenKnowledgeBase()
        
    def run(self, state: AgentState) -> dict:
        question = state.get("user_question", "")
        error = state.get("error")
        
        logger.info(f"Generating SQL for question: {question}")
        
        # Retrieve similar examples
        examples = self.golden_kb.find_similar_examples(question)
        logger.info(f"\n[Golden Knowledge Retrieved]:\n{examples[:300]}...\n") 
        
        system_prompt = """You are a BigQuery SQL Expert for a Retail Company.
        Your goal is to answer user questions by generating valid SQL queries for the `bigquery-public-data.thelook_ecommerce` dataset.
        
        Schema Overview:
        - `orders` (order_id, user_id, status, created_at, ...)
        - `order_items` (id, order_id, user_id, product_id, sale_price, status, ...)
        - `products` (id, cost, category, name, brand, retail_price, ...)
        - `users` (id, first_name, last_name, email, age, country, ...)
        
        Rules:
        1. Always use standard SQL. Remember about Google BigQuery syntax quirks.
        2. Date functions: Use `CURRENT_DATE()` or `TIMESTAMP_TRUNC`.
        3. If the user asks for "Revenue", check `order_items` where status is 'Complete'.
        4. Do NOT include PII in the SELECT clause if possible, but you can filter by it.
        5. Return ONLY the SQL query. No markdown formatting (```sql), no explanation.
        """
        
        # If this is a retry due to error, add the error context
        if error:
            logger.info(f"Retrying after error: {error}")
            # Escape curly braces in error message to prevent LangChain from treating them as variables
            safe_error = error.replace("{", "{{").replace("}", "}}")
            system_prompt += f"\n\nThe previous query failed with this error: {safe_error}. Please fix the SQL."

        user_prompt = f"{examples}\n\nQuestion: {question}\nSQL Query:"
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", user_prompt)
        ])
        
        # VV LangChain Expression to chain components
        chain = prompt | self.llm | StrOutputParser()
        
        try:
            logger.info("Calling Gemini API...")
            sql_query = chain.invoke({})
            logger.info(f"Received response from Gemini: {sql_query[:100] if sql_query else 'EMPTY'}")
            # Clean up markdown if the LLM adds it despite instructions
            sql_query = sql_query.replace("```sql", "").replace("```", "").strip()
            logger.info(f"\n[Generated SQL]:\n{sql_query}\n")
            return {"generated_sql": sql_query}
        except Exception as e:
            logger.error(f"Exception in SQL generator: {str(e)}", exc_info=True)
            return {"error": f"Failed to generate SQL: {str(e)}"}

def sql_generator_node(state: AgentState):
    generator = SQLGenerator()
    return generator.run(state)
