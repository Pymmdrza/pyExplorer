from flask import Flask
from app.config.config_manager import config
from app.utils.formatters import format_large_number

app = Flask(__name__, 
           template_folder='../templates',  # Updated template path
           static_folder='../static')       # Updated static path

# Add template filter for formatting large numbers
app.jinja_env.filters['format_large_number'] = format_large_number

from app.routes import *  # Import routes after app initialization