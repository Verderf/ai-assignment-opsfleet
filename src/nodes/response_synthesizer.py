from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from src.state import AgentState
import os
import yaml
import logging

class ResponseSynthesizer:
    def __init__(self):
        model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash") # just realized they've discontinued gemini-1.5 already! :/
        logging.info(f"Using Gemini model: {model_name}")
        self.llm = ChatGoogleGenerativeAI(
            model=model_name, 
            google_api_key=os.getenv("GOOGLE_API_KEY"),
            temperature=0.5
        )
        self.persona = self._load_persona()

    def _load_persona(self):
        try:
            # Load persona from config file - this allows easy customization on the fly
            with open("config/persona.yaml", "r") as f:
                return yaml.safe_load(f)
        except Exception:
            # generic agent persona description
            return {"role": "Assistant", "tone": "professional", "instructions": "Be helpful."}

    def run(self, state: AgentState) -> dict:
        question = state.get("user_question", "")
        results = state.get("query_result", [])
        error = state.get("error")
        
        if error:
            return {"final_answer": f"I encountered an error executing the query after multiple attempts: {error}"}
        
        prompt_text = """You are a {role}.
        Tone: {tone}
        Instructions: {instructions}
        
        User Question: {question}
        
        Data Retrieved (JSON format):
        {results}
        
        Please provide a response based on the data above.
        Do NOT mention SQL or technical details.
        """
        
        prompt = ChatPromptTemplate.from_messages([
            ("user", prompt_text)
        ])
        
        chain = prompt | self.llm | StrOutputParser()
        answer = chain.invoke({
            "question": question, 
            "results": str(results),
            "role": self.persona.get("role"),
            "tone": self.persona.get("tone"),
            "instructions": self.persona.get("instructions")
        })
        
        return {"final_answer": answer}

def response_synthesizer_node(state: AgentState):
    synthesizer = ResponseSynthesizer()
    return synthesizer.run(state)
