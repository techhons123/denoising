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
h1 { color: #333; }
.upload-area { border: 2px dashed #ccc; padding: 20px; cursor: pointer; }
.button { background: #4285f4; color: white; padding: 10px; border: none; border-radius: 5px; cursor: pointer; }
.error-message { color: red; }
"""

# Index HTML
INDEX_HTML = """ 
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Image Denoiser</title>
    <style>{{ css }}</style>
</head>
<body>
    <div class="container">
        <h1>Image Denoiser</h1>
        {% if error %}<div class="error-message">{{ error }}</div>{% endif %}
        <form action="/" method="POST" enctype="multipart/form-data">
            <div class="upload-area" onclick="document.getElementById('file-input').click()">
                Click to select an image (max 16MB)
            </div>
            <input type="file" id="file-input" name="image" accept="image/*" required>
            <button type="submit" class="button">Upload & Denoise</button>
        </form>
    </div>
</body>
</html>
"""

# Image Processing Function
def denoise_image(input_path, output_path):
    """Apply denoising filters to the image."""
    try:
        image = cv2.imread(input_path)
        if image is None:
            raise ValueError("Failed to load image.")

        # Denoising using Non-Local Means
        denoised = cv2.fastNlMeansDenoisingColored(image, None, 10, 10, 7, 21)
        cv2.imwrite(output_path, denoised)
        return True, "Processing completed successfully"
    except Exception as e:
        logger.error(f"Error processing image: {str(e)}")
        return False, str(e)

# Routes
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'image' not in request.files:
            return render_template_string(INDEX_HTML, css=CSS_STYLE, error="No file selected")

        file = request.files['image']
        if file.filename == '':
            return render_template_string(INDEX_HTML, css=CSS_STYLE, error="No file selected")

        filename = secure_filename(file.filename)
        input_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        output_path = os.path.join(app.config['PROCESSED_FOLDER'], filename)

        file.save(input_path)
        success, message = denoise_image(input_path, output_path)

        if success:
            return f"Image processed successfully! <a href='/processed/{filename}'>Download</a>"
        else:
            return render_template_string(INDEX_HTML, css=CSS_STYLE, error=message)

    return render_template_string(INDEX_HTML, css=CSS_STYLE)

@app.route('/processed/<filename>')
def processed_file(filename):
    return send_from_directory(app.config['PROCESSED_FOLDER'], filename)

# Run the Flask app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
