import os
import cv2
import numpy as np
from flask import Flask, request, send_from_directory, render_template_string
from werkzeug.utils import secure_filename
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Flask setup
app = Flask(__name__)

# Use Render-compatible temp directories
app.config['UPLOAD_FOLDER'] = '/tmp/uploads'
app.config['PROCESSED_FOLDER'] = '/tmp/processed'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB limit

# Ensure directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['PROCESSED_FOLDER'], exist_ok=True)

# CSS Style
CSS_STYLE = """ 
body { font-family: Arial, sans-serif; background-color: #f0f0f0; }
.container { background: white; padding: 20px; border-radius: 5px; }
h1 { color: #333; }
.upload-area { border: 2px dashed #ccc; padding: 20px; cursor: pointer; }
.button { background: #4285f4; color: white; padding: 10px; border: none; border-radius: 5px; cursor: pointer; }
.error-message { color: red; }
"""

# HTML Template
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
            <input type="file" id="file-input" name="image" accept="image/*" required style="display:none;">
            <button type="submit" class="button">Upload & Denoise</button>
        </form>
    </div>
</body>
</html>
"""

# Image Processing
def denoise_image(input_path, output_path):
    try:
        image = cv2.imread(input_path)
        if image is None:
            raise ValueError("Failed to load image. Make sure the file is a valid image.")

        denoised = cv2.fastNlMeansDenoisingColored(image, None, 10, 10, 7, 21)
        cv2.imwrite(output_path, denoised)
        return True, "Image processed successfully."
    except Exception as e:
        logger.error(f"Error during image processing: {e}")
        return False, str(e)

# Routes
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'image' not in request.files:
            return render_template_string(INDEX_HTML, css=CSS_STYLE, error="No file uploaded.")

        file = request.files['image']
        if file.filename == '':
            return render_template_string(INDEX_HTML, css=CSS_STYLE, error="No file selected.")

        filename = secure_filename(file.filename)
        input_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        output_path = os.path.join(app.config['PROCESSED_FOLDER'], filename)

        try:
            file.save(input_path)
            success, message = denoise_image(input_path, output_path)
            if success:
                return f"Image processed successfully! <a href='/processed/{filename}'>Download</a>"
            else:
                return render_template_string(INDEX_HTML, css=CSS_STYLE, error=message)
        except Exception as e:
            logger.error(f"File handling error: {e}")
            return render_template_string(INDEX_HTML, css=CSS_STYLE, error="An error occurred during upload or processing.")

    return render_template_string(INDEX_HTML, css=CSS_STYLE)

@app.route('/processed/<filename>')
def processed_file(filename):
    return send_from_directory(app.config['PROCESSED_FOLDER'], filename)

# App entry point
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
