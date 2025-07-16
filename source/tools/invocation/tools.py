import subprocess
import sys
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
    except Exception as e:
        return f"Error opening {clean_app_name}: {e}. The name might be wrong or the app might not be installed"
