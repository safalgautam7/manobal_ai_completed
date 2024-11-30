
import random
from pydantic import BaseModel







# Function to load quotes from the file
def load_quotes_from_file(filename):
    """Load quotes from a file and return them as a list."""
    with open(filename, "r", encoding="utf-8") as file:
        quotes = file.readlines()
    return quotes

# Function to return a random quote
def get_random_quote(quotes):
    """Returns a randomly selected quote from the list."""
    return random.choice(quotes).strip()

# Define the endpoint to get a random quote

