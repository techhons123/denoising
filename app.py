
import os
import cv2
import numpy as np
from flask import Flask, request, send_from_directory, render_template_string, jsonify
from werkzeug.utils import secure_filename
import time
from threading import Thread
import logging
from datetime import datetime
# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['PROCESSED_FOLDER'] = 'processed'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Limit uploads to 16MB
# Create directories if they don't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['PROCESSED_FOLDER'], exist_ok=True)
# Job status tracking
processing_jobs = {}
# CSS Style
CSS_STYLE = """ 
body { font-family: Arial, sans-serif; background-color: #f0f0f0; }
.container { background: white; padding: 20px; border-radius: 5px; }
