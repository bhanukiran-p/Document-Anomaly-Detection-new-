import sys
print(f"Python executable: {sys.executable}")
print(f"Python version: {sys.version}")

try:
    print("Attempting to import from langchain_core.prompts...")
    from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
    print("Successfully imported prompts from langchain_core")
    
    print("Attempting to import ChatOpenAI...")
    from langchain_openai import ChatOpenAI
    print("Successfully imported ChatOpenAI")

except ImportError as e:
    print(f"ImportError: {e}")
except Exception as e:
    print(f"Exception: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
