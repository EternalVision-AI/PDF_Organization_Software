from langchain_ollama import OllamaLLM
import json

# Load the JSON file
with open("config.json", "r") as file:
    config = json.load(file)

# Access the categories array
categories = config.get("categories", [])
# content = "An agreement to ensure all shared information remains private."
# Initialize the model
llm = OllamaLLM(model="llama3.1")


def llm_classifier(content):
    # Define the prompt with explicit output instructions
    prompt = f"""
    # Task
    Categorize the provided germany document content based on the following predefined categories. 
    Provide your answer as the **category name of {categories} only** without any explanation or additional text. If no match is found, respond with Uncategorized.

    # Document Content
    {content}

    # Categories
    {categories}

    # Instruction
    Provide your answer as the **category name of {categories} only** without any explanation or additional text. If no match is found, respond with Uncategorized.
    """

    # Invoke the model with the prompt
    response = llm.invoke(prompt)

    # Print the response
    print(response.strip())  # Stripping whitespace for cleaner output
    return response.strip()
