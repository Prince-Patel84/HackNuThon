from flask import Flask, render_template, request, send_from_directory, redirect, url_for, jsonify
from werkzeug.utils import secure_filename
import os
import shutil
from datetime import datetime
import json
from pathlib import Path
from functools import wraps

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "pdf", "doc", "docx", "txt", "zip", "rar", "pptx"}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
ADMIN_PASSWORD = "123456"  # Change this to your desired password

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

# Home route - Show folders & files
@app.route("/", defaults={"folder": ""})
@app.route("/<path:folder>")
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
        return jsonify({"error": str(e)}), 404

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
