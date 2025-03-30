from flask import Flask, render_template, request, send_from_directory, redirect, url_for, jsonify, send_file
from werkzeug.utils import secure_filename
import os
import shutil
from datetime import datetime
import json
from pathlib import Path
from functools import wraps
import qrcode
from io import BytesIO
import base64
from PIL import Image, ImageDraw, ImageFont
from cryptography.fernet import Fernet

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "pdf", "doc", "docx", "txt", "zip", "rar", "pptx"}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
ADMIN_PASSWORD = "123456"  # Change this to your desired password
MASTER_PASSWORD = "Prince@123"  # Set your master password here
FILE_PASSWORD = "file@123"  # Default file password
ENCRYPTION_KEY = Fernet.generate_key()  # Generate a key for encryption
fernet = Fernet(ENCRYPTION_KEY)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = MAX_FILE_SIZE

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Password protection decorator
def require_password(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        password = request.form.get('password')
        if not password or password != ADMIN_PASSWORD:
            return jsonify({"error": "Invalid password"}), 403
        return f(*args, **kwargs)
    return decorated_function

# Check allowed file types
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def get_file_info(filepath):
    """Get file metadata including size, creation date, and last modified date."""
    stats = os.stat(filepath)
    return {
        "size": stats.st_size,
        "created": datetime.fromtimestamp(stats.st_ctime).strftime("%Y-%m-%d %H:%M:%S"),
        "modified": datetime.fromtimestamp(stats.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
    }

def format_size(size):
    """Format file size in human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} TB"

# Home route - Show home page
@app.route("/")
def home():
    return render_template("home.html")

# File browser route - Show folders & files
@app.route("/browser", defaults={"folder": ""})
@app.route("/browser/<path:folder>")
def list_files(folder):
    try:
        folder_path = os.path.join(app.config["UPLOAD_FOLDER"], folder)

        if not os.path.exists(folder_path):
            return render_template("index.html", 
                                 folder=folder,
                                 folders=[],
                                 files=[],
                                 error="Folder does not exist!"), 404

        items = os.listdir(folder_path)
        folders = []
        files = []

        for item in items:
            item_path = os.path.join(folder_path, item)
            if os.path.isdir(item_path):
                folders.append(item)
            else:
                file_info = get_file_info(item_path)
                files.append({
                    "name": item,
                    "info": file_info,
                    "formatted_size": format_size(file_info["size"])
                })

        # Sort folders alphabetically
        folders.sort()
        
        # Sort files by name
        files.sort(key=lambda x: x["name"].lower())

        return render_template("index.html", 
                             folder=folder, 
                             folders=folders, 
                             files=files,
                             current_path=folder)
    except Exception as e:
        return render_template("index.html", 
                             folder=folder,
                             folders=[],
                             files=[],
                             error=str(e)), 500

@app.route("/verify_password", methods=["POST"])
def verify_password():
    password = request.form.get('password')
    if password == ADMIN_PASSWORD:
        return jsonify({"success": True})
    return jsonify({"error": "Invalid password"}), 403

# Upload file
@app.route("/upload", methods=["POST"])
@require_password
def upload_file():
    try:
        folder = request.form.get("folder", "").strip()
        
        # Prevent file uploads in root directory
        if not folder:
            return jsonify({"error": "Files can only be uploaded inside folders"}), 400

        folder_path = os.path.join(app.config["UPLOAD_FOLDER"], folder)

        if "file" not in request.files:
            return jsonify({"error": "No file part"}), 400

        files = request.files.getlist("file")
        if not files or all(file.filename == "" for file in files):
            return jsonify({"error": "No selected files"}), 400

        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

        uploaded_files = []
        for file in files:
            if file and file.filename != "" and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_path = os.path.join(folder_path, filename)
                
                # Check if file already exists
                if os.path.exists(file_path):
                    base, ext = os.path.splitext(filename)
                    counter = 1
                    while os.path.exists(file_path):
                        filename = f"{base}_{counter}{ext}"
                        file_path = os.path.join(folder_path, filename)
                        counter += 1

                file.save(file_path)
                uploaded_files.append(filename)
            else:
                return jsonify({"error": f"File type not allowed: {file.filename}"}), 400

        return jsonify({
            "success": True,
            "message": f"Successfully uploaded {len(uploaded_files)} files",
            "files": uploaded_files
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Delete File or Folder
@app.route("/delete", methods=["POST"])
@require_password
def delete_item():
    try:
        folder = request.form.get("folder", "").strip()
        item_name = request.form.get("item").strip()
        item_path = os.path.join(app.config["UPLOAD_FOLDER"], folder, item_name)

        if not os.path.exists(item_path):
            return jsonify({"error": "Item does not exist"}), 404

        if os.path.isdir(item_path):
            shutil.rmtree(item_path)
        else:
            os.remove(item_path)

        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Create Folder
@app.route("/create_folder", methods=["POST"])
@require_password
def create_folder():
    try:
        folder = request.form.get("folder", "").strip()
        new_folder = request.form.get("new_folder").strip()
        
        # Only allow folder creation in root directory
        if folder:
            return jsonify({"error": "Folders can only be created in the root directory"}), 400
        
        if not new_folder:
            return jsonify({"error": "Folder name is required"}), 400

        folder_path = os.path.join(app.config["UPLOAD_FOLDER"], new_folder)
        
        if os.path.exists(folder_path):
            return jsonify({"error": "Folder already exists"}), 400

        os.makedirs(folder_path)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Serve uploaded files
@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    try:
        return send_from_directory(app.config["UPLOAD_FOLDER"], filename)
    except Exception as e:
        return str(e), 404

@app.route("/download/<path:filename>")
def download_file(filename):
    try:
        return send_from_directory(app.config["UPLOAD_FOLDER"], filename, as_attachment=True)
    except Exception as e:
        return str(e), 404

# Rename File or Folder
@app.route("/rename", methods=["POST"])
@require_password
def rename_item():
    try:
        folder = request.form.get("folder", "").strip()
        old_name = request.form.get("old_name").strip()
        new_name = request.form.get("new_name").strip()
        is_folder = request.form.get("is_folder") == "true"

        if not old_name or not new_name:
            return jsonify({"error": "Old and new names are required"}), 400

        # Get the full paths
        old_path = os.path.join(app.config["UPLOAD_FOLDER"], folder, old_name)
        new_path = os.path.join(app.config["UPLOAD_FOLDER"], folder, new_name)

        # Check if old path exists
        if not os.path.exists(old_path):
            return jsonify({"error": "Item does not exist"}), 404

        # If renaming a file (not a folder), preserve the extension
        if not is_folder:
            old_ext = os.path.splitext(old_name)[1]
            if not new_name.endswith(old_ext):
                new_name = new_name + old_ext
                new_path = os.path.join(app.config["UPLOAD_FOLDER"], folder, new_name)

        # Check if new name already exists
        if os.path.exists(new_path):
            return jsonify({"error": "An item with this name already exists"}), 400

        # Rename the item
        os.rename(old_path, new_path)

        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Remove File Extension
@app.route("/remove_extension", methods=["POST"])
@require_password
def remove_extension():
    try:
        folder = request.form.get("folder", "").strip()
        filename = request.form.get("filename").strip()
        
        if not filename:
            return jsonify({"error": "Filename is required"}), 400

        # Get the full paths
        old_path = os.path.join(app.config["UPLOAD_FOLDER"], folder, filename)
        
        # Check if file exists
        if not os.path.exists(old_path):
            return jsonify({"error": "File does not exist"}), 404
            
        # Check if it's a file (not a folder)
        if os.path.isdir(old_path):
            return jsonify({"error": "Cannot remove extension from a folder"}), 400
            
        # Get the new name without extension
        new_name = os.path.splitext(filename)[0]
        new_path = os.path.join(app.config["UPLOAD_FOLDER"], folder, new_name)
        
        # Check if new name already exists
        if os.path.exists(new_path):
            return jsonify({"error": "A file with this name already exists"}), 400
            
        # Rename the file
        os.rename(old_path, new_path)
        
        return jsonify({
            "success": True,
            "message": f"Extension removed from {filename}"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/generate_qr", methods=["POST"])
def generate_qr():
    try:
        folder = request.form.get("folder", "").strip()
        # Generate the full URL for the folder, ensuring proper path formatting
        folder_url = request.host_url.rstrip('/') + '/browser/' + folder.lstrip('/') if folder else request.host_url.rstrip('/')
        
        # Create QR code
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(folder_url)
        qr.make(fit=True)
        
        # Create image with extra space for text
        img = qr.make_image(fill_color="black", back_color="white")
        width, height = img.size
        new_height = height + 120  # Increased space for larger text
        
        # Create new image with white background
        new_img = Image.new('RGB', (width, new_height), 'white')
        
        # Convert QR code to RGB mode if it isn't already
        if img.mode != 'RGB':
            img = img.convert('RGB')
            
        # Paste QR code at the top
        new_img.paste(img, (0, 0))
        
        # Add text
        draw = ImageDraw.Draw(new_img)
        
        # Get folder name from path
        folder_name = folder.split('/')[-1] if folder else "Home"
        
        # Use default font
        font = ImageFont.load_default()
        
        # Calculate text position to center it
        text_width = len(folder_name) * 20  # Increased width per character for larger text
        text_position = ((width - text_width) // 2, height + 30)  # Adjusted vertical position
        
        # Draw text
        draw.text(text_position, folder_name, fill="black", font=font)
        
        # Convert to base64
        buffered = BytesIO()
        new_img.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        return jsonify({"success": True, "qr_code": img_str})
    except Exception as e:
        print(f"QR Code Generation Error: {str(e)}")  # Add error logging
        return jsonify({"error": str(e)}), 500

@app.route("/search", methods=["GET"])
def search():
    query = request.args.get("q", "").lower()
    results = {"files": [], "folders": []}
    
    def search_directory(current_path, relative_path=""):
        items = os.listdir(current_path)
        
        for item in items:
            item_path = os.path.join(current_path, item)
            relative_item_path = os.path.join(relative_path, item)
            
            if os.path.isdir(item_path):
                if query in item.lower():
                    results["folders"].append({
                        "name": item,
                        "path": relative_item_path
                    })
                search_directory(item_path, relative_item_path)
            else:
                if query in item.lower():
                    file_info = get_file_info(item_path)
                    results["files"].append({
                        "name": item,
                        "path": relative_item_path,
                        "info": file_info,
                        "formatted_size": format_size(file_info["size"])
                    })
    
    try:
        search_directory(app.config["UPLOAD_FOLDER"])
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/filter")
def filter_files():
    filter_type = request.args.get("type", "all")
    results = {"files": []}
    
    # Define file extensions for each type
    type_extensions = {
        "pdf": ["pdf"],
        "doc": ["doc", "docx"],
        "zip": ["zip", "rar"],
        "image": ["png", "jpg", "jpeg", "gif"],
        "txt": ["txt"],
        "pptx": ["pptx"]
    }
    
    def scan_directory(current_path, relative_path=""):
        items = os.listdir(current_path)
        
        for item in items:
            item_path = os.path.join(current_path, item)
            relative_item_path = os.path.join(relative_path, item)
            
            if os.path.isdir(item_path):
                scan_directory(item_path, relative_item_path)
            else:
                extension = item.split('.')[-1].lower() if '.' in item else ""
                if filter_type == "all" or extension in type_extensions.get(filter_type, []):
                    file_info = get_file_info(item_path)
                    results["files"].append({
                        "name": item,
                        "path": relative_item_path,
                        "info": file_info,
                        "formatted_size": format_size(file_info["size"])
                    })
    
    try:
        scan_directory(app.config["UPLOAD_FOLDER"])
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/protected_download/<path:filename>")
def protected_download(filename):
    password = request.args.get('password')
    
    if not password or password != FILE_PASSWORD:
        return jsonify({"error": "Invalid password"}), 403
        
    try:
        file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        if not os.path.exists(file_path):
            return jsonify({"error": "File not found"}), 404
            
        # Read and encrypt the file
        with open(file_path, 'rb') as file:
            file_data = file.read()
            encrypted_data = fernet.encrypt(file_data)
            
        response = send_file(
            BytesIO(encrypted_data),
            as_attachment=True,
            download_name=os.path.basename(filename),
            mimetype='application/octet-stream'
        )
        
        return response
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.errorhandler(413)
def request_entity_too_large(error):
    return jsonify({"error": "File too large"}), 413

@app.errorhandler(404)
def not_found_error(error):
    return render_template("index.html", 
                         folder="",
                         folders=[],
                         files=[],
                         error="Page not found"), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template("index.html", 
                         folder="",
                         folders=[],
                         files=[],
                         error="Internal server error"), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
