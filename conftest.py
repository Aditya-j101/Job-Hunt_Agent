# conftest.py
import sys
import os

# adds the project root to Python's import path
# so pytest can find models/, graph/, utils/ etc.
sys.path.insert(0, os.path.dirname(__file__))