import os
import cv2
import numpy as np
from flask import Flask, request, send_from_directory, render_template_string
from werkzeug.utils import secure_filename
import logging

# Flask setup
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = '/tmp/uploads'
app.config['PROCESSED_FOLDER'] = '/tmp/processed'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ensure directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['PROCESSED_FOLDER'], exist_ok=True)

# Modern Bootstrap HTML template
HTML_TEMPLATE = """
<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <title>Image Denoiser</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link 
        href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" 
        rel="stylesheet">
    <style>
        body { background-color: #f8f9fa; }
        .container { margin-top: 50px; max-width: 600px; }
        .preview-img { max-width: 100%; max-height: 300px; margin-top: 20px; }
    </style>
</head>
<body>
<div class="container">
    <h2 class="mb-4 text-center">🧼 Image Denoiser</h2>
    {% if error %}
        <div class="alert alert-danger">{{ error }}</div>
    {% endif %}
    {% if success %}
        <div class="alert alert-success">
            {{ success }}<br>
            <a href="/processed/{{ filename }}" class="btn btn-sm btn-primary mt-2">Download Image</a>
        </div>
    {% endif %}
    <form method="POST" enctype="multipart/form-data">
        <div class="mb-3">
            <label for="file-input" class="form-label">Choose an image</label>
            <input class="form-control" type="file" id="file-input" name="image" accept="image/*" required>
        </div>
        <div id="preview"></div>
        <button type="submit" class="btn btn-primary w-100">Upload & Denoise</button>
    </form>
</div>
<script>
document.getElementById('file-input').addEventListener('change', function(event) {
    const preview = document.getElementById('preview');
    preview.innerHTML = '';
    const file = event.target.files[0];
    if (file) {
        const img = document.createElement('img');
        img.classList.add('preview-img');
        img.src = URL.createObjectURL(file);
        preview.appendChild(img);
    }
});
</script>
</body>
</html>
"""

def denoise_image(input_path, output_path):
    try:
        image = cv2.imread(input_path)
        if image is None:
            raise ValueError("Invalid image file.")
        denoised = cv2.fastNlMeansDenoisingColored(image, None, 10, 10, 7, 21)
        cv2.imwrite(output_path, denoised)
        return True, "Image processed successfully"
    except Exception as e:
        logger.error(f"Denoising failed: {e}")
        return False, str(e)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'image' not in request.files:
            return render_template_string(HTML_TEMPLATE, error="No file part")

        file = request.files['image']
        if file.filename == '':
            return render_template_string(HTML_TEMPLATE, error="No selected file")

        filename = secure_filename(file.filename)
        input_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        output_path = os.path.join(app.config['PROCESSED_FOLDER'], filename)

        file.save(input_path)
        success, message = denoise_image(input_path, output_path)
        if success:
            return render_template_string(HTML_TEMPLATE, success=message, filename=filename)
        else:
            return render_template_string(HTML_TEMPLATE, error=message)

    return render_template_string(HTML_TEMPLATE)

@app.route('/processed/<filename>')
def processed_file(filename):
    return send_from_directory(app.config['PROCESSED_FOLDER'], filename)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
