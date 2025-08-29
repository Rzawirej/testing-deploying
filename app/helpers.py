from dotenv import load_dotenv
import os

load_dotenv()
something = os.getenv('SOMETHING', '')
def calculate_returned_value():
    return f"<p>{something}</p>"