import subprocess
import sys
from duckduckgo_search import DDGS
import os
from datetime import datetime

from langchain_core.tools import tool

# agent tools for invoking and using inhouse application

@tool
def get_current_time() -> str:
    """ Returns the current time in a human readable format."""
    return datetime.now().strftime("%I:%M %p")

@tool
def open_application(app_name: str) -> str:
    """
    Opens an application on the user's computer.
    'app_name' should be the name of the application , e.g., 'Notepad' , 'Brave' , 'Terminal'
    """
    try:
        clean_app_name = app_name.strip().strip("\"")
        os.startfile(clean_app_name)
        return f"The application '{clean_app_name}' has been successfully opened."
    except Exception as e:
        return f"Error opening {clean_app_name}: {e}. The name might be wrong or the app might not be installed"

@tool
def search_internet(query: str) -> str:
    """
    Searches the internet using duckduckgo fo a given query and returns the top 3-5 results.
    Use this for questions about current events, facts or information not known to the AI
    """
    print(f"Searching internet for : {query}")
    with DDGS() as ddgs:
        results = [search_result['body'] for search_result in ddgs.text(query, region="us-en", max_results=5)]
        return "\n".join(results) if results else "No results found"
