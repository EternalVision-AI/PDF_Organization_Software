import sqlite3
from langchain_ollama import OllamaLLM
import json

# Ensure necessary NLTK resources are downloaded
""" Use the LLaMA model to categorize the document. """
llm = OllamaLLM(model="llama3.1")

def setup_database():
    """ Set up SQLite database """
    conn = sqlite3.connect('documents.db')
    c = conn.cursor()
    c.execute('''
    CREATE TABLE IF NOT EXISTS documents (
        filename TEXT UNIQUE,
        category TEXT,
        summary TEXT
    )
    ''')
    conn.commit()
    conn.close()

def load_config(file_path):
    """ Load the configuration from a JSON file. """
    with open(file_path, "r") as file:
        config = json.load(file)
    return config

setup_database()
config = load_config("config.json")
categories = config.get("categories", [])
    
def fetch_all_categories_and_summaries():
    """ Fetch all categories and summaries from the database. """
    conn = sqlite3.connect('documents.db')
    c = conn.cursor()
    c.execute('SELECT category, summary FROM documents')
    all_data = c.fetchall()
    conn.close()
    return all_data
    
def create_prompt(content, categories):
    """ Generate a detailed prompt for the model including references to historical data. """
    all_data = fetch_all_categories_and_summaries()
    historical_context = ""
    for category, summary in all_data:
        historical_context += f"Summary: {summary}, Category: {category}\n"
        
    categories_str = ', '.join(categories)
    prompt = f"""
    ### Historical Data ###
    Below is historical context to aid in categorization:
    {historical_context}
    
    ### Task ###
    You are a categorization expert. Analyze the provided document content and determine the most appropriate category. 
    Categorize the provided document content based on the following predefined categories:
    {categories_str}

    Provide your answer as the category name only. If no suitable category is found, respond with 'Uncategorized'.

    ### Document Content ###
    {content}

    ### Categories ###
    {categories_str}

    ### Instruction ###
    Provide your answer as the category name only without any additional text.
    """
    return prompt

def categorize_document(content):
    
    prompt = create_prompt(content, categories)
    response = llm.invoke(prompt)
    return response.strip()

def create_summary_prompt(content, num_sentences):
    """
    Create a prompt for generating a concise summary of the given text.
    """
    return (
        f"### Instruction ###\n"
        f"You are an expert summarizer. Summarize the given content into exactly {num_sentences} sentences.\n"
        f"Make sure the summary is concise, accurate, and captures the key points effectively.\n"
        f"### Content ###\n"
        f"{content.strip()}\n"
        f"### Output ###\n"
        f"[Start your summary here:]\n"
    )


def get_summary(content, num_sentences=1):
    """ Generate a summary"""
    prompt = create_summary_prompt(content, num_sentences)
    response = llm.invoke(prompt)
    return response.strip()
    return summary

def save_document_info(filename, category, summary):
    """ Save or update document information in the database based on filename """
    conn = sqlite3.connect('documents.db')
    c = conn.cursor()
    # Use UPSERT functionality to update existing records or insert new ones
    c.execute('''
    INSERT INTO documents (filename, category, summary) VALUES (?, ?, ?)
    ON CONFLICT(filename) DO UPDATE SET
    category=excluded.category, summary=excluded.summary
    ''', (filename, category, summary))
    conn.commit()
    conn.close()

def process_document(filename, content):
    """ Process the document to categorize and summarize """
    category = categorize_document(content)
    summary = get_summary(content)
    save_document_info(filename, category, summary)
    print(f"Processed {filename} categorized as {category} with summary: {summary}")
    return category

# if __name__ == "__main__":
    
#     filename = "Independant_Contract_NDA.pdf"
#     content = "You need to pay $300 for power."
#     process_document(filename, content)
