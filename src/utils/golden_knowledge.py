from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
import os
import yaml
import logging

class GoldenKnowledgeBase:
    """
    Implements Semantic Search over the Golden Knowledge Base using FAISS and Gemini Embeddings.
    Loads data from 'data/golden_trios.yaml'.
    """
    
    def __init__(self):
        self.vector_store = None
        self._initialize_knowledge_base()

    def _initialize_knowledge_base(self):
        """
        Loads YAML data, generates embeddings, and builds the FAISS index.
        Caches the index to disk to avoid hitting API rate limits on restart.
        """
        # 0. Check for FAISS availability before doing anything expensive
        try:
            import faiss
        except ImportError:
            logging.warning("FAISS library not found. Skipping Golden Knowledge initialization to save API quota.")
            return

        try:
            api_key = os.getenv("GOOGLE_API_KEY")
            if not api_key:
                logging.error("GOOGLE_API_KEY not found. Cannot initialize embeddings.")
                return

            embeddings = GoogleGenerativeAIEmbeddings(
                model="models/text-embedding-004", 
                google_api_key=api_key
            )
            
            index_path = os.path.join("data", "faiss_index")
            
            # Check if cached index exists
            if os.path.exists(index_path):
                logging.info("Loading FAISS index from local cache...")
                try:
                    self.vector_store = FAISS.load_local(
                        index_path, 
                        embeddings, 
                        allow_dangerous_deserialization=True # Safe since we created it
                    )
                    return
                except Exception as e:
                    logging.warning(f"Failed to load cached index: {e}. Rebuilding...")

            # Load Data
            yaml_path = os.path.join("data", "golden_trios.yaml")
            if not os.path.exists(yaml_path):
                logging.warning(f"Golden bucket file not found at {yaml_path}. Using empty base.")
                return

            with open(yaml_path, "r") as f:
                trios = yaml.safe_load(f)

            if not trios:
                logging.warning("Golden bucket file is empty.")
                return

            # Prepare Documents for Vector Store
            documents = []
            for item in trios:
                # The 'page_content' is what we embed (the question)
                # The 'metadata' holds the SQL and Insight to retrieve
                doc = Document(
                    page_content=item["question"],
                    metadata={"sql": item["sql"], "insight": item.get("insight", "")}
                )
                documents.append(doc)

            # Build FAISS Index
            logging.info(f"Building FAISS index with {len(documents)} examples...")
            self.vector_store = FAISS.from_documents(documents, embeddings)
            
            # Save to disk
            self.vector_store.save_local(index_path)
            logging.info("FAISS index built and saved successfully.")

        except Exception as e:
            logging.error(f"Failed to initialize Golden Knowledge Base: {str(e)}")

    def find_similar_examples(self, query: str, k: int = 2) -> str:
        """
        Performs semantic search to find relevant examples. 2 top matches are returned by default.
        """
        if not self.vector_store:
            return "No historical examples available (Knowledge Base not initialized)."

        try:
            # Semantic Search
            results = self.vector_store.similarity_search(query, k=k)
            
            output_text = "Here are similar queries written by our analysts (Golden Knowledge):\n\n"
            for doc in results:
                output_text += f"Q: {doc.page_content}\nSQL: {doc.metadata['sql']}\nInsight: {doc.metadata['insight']}\n\n"
            
            return output_text
        except Exception as e:
            logging.error(f"Error during semantic search: {str(e)}")
            return "Error retrieving examples."
