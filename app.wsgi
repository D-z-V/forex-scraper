import os
import sys
from fastapi import FastAPI

# Add the app directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import app

app = app
