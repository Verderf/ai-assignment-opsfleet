import os
import sys
from dotenv import load_dotenv
from src.graph import create_graph

# Load environment variables
load_dotenv()

def main():
    print("Welcome to the Retail Data Analysis Agent! Proudly presented by Dmitrii Shtom :D ")
    print("-----------I hope it works as expected---------------")
    print("-----------------------------------------------------")
    
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("CRITICAL: GOOGLE_API_KEY is not set. Please set it in .env file.")
        # Proceeding might fail, but let's allow it to start so user sees the prompt.
    
    # Initialize the Graph
    app = create_graph()
    
    print("Type 'exit' to quit.")
    
    while True:
        try:
            user_input = input("\nYou: ")
            if user_input.lower() in ["exit", "quit"]:
                break
                
            print("Agent: Thinking...")
            
            # Initial State
            initial_state = {
                "user_question": user_input,
                "messages": [],
                "retry_count": 0,
                "error": None
            }
            
            # Run the Graph
            result = app.invoke(initial_state)
            
            # Display Output
            final_answer = result.get("final_answer", "No answer generated.")
            print(f"\nAgent: {final_answer}")
            
            # Debug/Transparency Info
            if result.get("generated_sql"):
                print(f"\n[Debug] Generated SQL:\n{result['generated_sql']}")
            if result.get("error"):
                print(f"\n[Debug] Final Error State: {result['error']}")
                
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
