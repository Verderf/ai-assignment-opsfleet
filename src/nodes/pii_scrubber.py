import re
import pandas as pd
from src.state import AgentState

class PIIScrubber:
    def __init__(self):
        # Pre-compile regex for speed
        self.email_pattern = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
        self.phone_pattern = re.compile(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b')
        
        # Exact column matches (Case insensitive). Retrieved this by listing schema of thelook_ecommerce.users tables.
        self.pii_columns = {
            "email", "phone", "first_name", "last_name", "credit_card", "ssn", "fullname",
            "street_address", "address", "zip_code", "postal_code", "ip_address"
        }

    def run(self, state: AgentState) -> dict:
        results = state.get("query_result")
        if not results:
            return {"query_result": results}
        
        # Convert list of dicts to DataFrame for vectorized scrubbing
        df = pd.DataFrame(results)
        
        if df.empty:
            return {"query_result": results}
            
        # 1. Hard Redaction: Redact entire columns based on name
        # We check if any column header *contains* a blocked word (e.g. "customer_email")
        cols_to_scrub = [c for c in df.columns if any(p in c.lower() for p in self.pii_columns)]
        
        for col in cols_to_scrub:
            df[col] = f"[REDACTED_{col.upper()}]"

        # 2. Soft Redaction: Scan remaining string columns for patterns
        # Only apply to object (string) columns to save time
        str_cols = df.select_dtypes(include=['object']).columns
        
        # Remove the columns we already scrubbed from this check
        str_cols = [c for c in str_cols if c not in cols_to_scrub]

        for col in str_cols:
            # Apply regex substitution (vectorized)
            # This turns "Contact bob@gmail.com" into "Contact [EMAIL]"
            # We treat non-string values gracefully
            df[col] = df[col].astype(str).apply(
                lambda x: self.email_pattern.sub("[REDACTED_EMAIL]", x)
            )
            df[col] = df[col].apply(
                lambda x: self.phone_pattern.sub("[REDACTED_PHONE]", str(x))
            )
            
        # Convert back to list of dicts
        scrubbed_results = df.to_dict(orient='records')
        return {"query_result": scrubbed_results}

def pii_scrubber_node(state: AgentState):
    scrubber = PIIScrubber()
    return scrubber.run(state)
