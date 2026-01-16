import os
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, flash
from werkzeug.utils import secure_filename
from pathlib import Path
from datetime import datetime
import redis

# Configuration
BASE_DIR = Path(__file__).resolve().parent
UPLOAD_ROOT = BASE_DIR / "uploads"
FOLDER_COUNT = 6
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "bmp", "webp"}

REDIS_HOST = 'redis'
REDIS_PORT = 6379
r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)


# Create upload folders if missing
for i in range(1, FOLDER_COUNT + 1):
    (UPLOAD_ROOT / f"folder{i}").mkdir(parents=True, exist_ok=True)

app = Flask(__name__)
app.secret_key = "change-me-to-a-secure-random-value"  # for flash messages


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def get_files_in_folder(folder_name: str):
    folder_path = UPLOAD_ROOT / folder_name
    files = []
    if folder_path.exists():
        for p in sorted(folder_path.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True):
            if p.is_file():
                files.append({
                    "name": p.name,
                    "size_kb": round(p.stat().st_size / 1024, 1),
                    "mtime": datetime.fromtimestamp(p.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                })
    return files


@app.route("/")
def index():
    folders = [{"name": f"folder{i}", "display": f"Folder {i}"} for i in range(1, FOLDER_COUNT + 1)]
    return render_template("index.html", folders=folders)


@app.route("/folder/<int:folder_id>", methods=["GET", "POST"])
def folder_view(folder_id):
    if folder_id < 1 or folder_id > FOLDER_COUNT:
        flash("Invalid folder id", "danger")
        return redirect(url_for("index"))

    folder_name = f"folder{folder_id}"
    folder_path = UPLOAD_ROOT / folder_name

    if request.method == "POST":
        if "file" not in request.files:
            flash("No file part in request", "warning")
            return redirect(request.url)

        file = request.files["file"]
        if file.filename == "":
            flash("No file selected", "warning")
            return redirect(request.url)

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            # Add timestamp prefix to avoid collisions
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            final_name = f"{timestamp}_{filename}"
            destination = folder_path / final_name
            file.save(destination)
            flash(f"Uploaded {final_name} to {folder_name}", "success")
            return redirect(request.url)
        else:
            flash("File type not allowed. Allowed: " + ", ".join(sorted(ALLOWED_EXTENSIONS)), "danger")
            return redirect(request.url)

    # GET
    files = get_files_in_folder(folder_name)
    return render_template("folder.html", folder_id=folder_id, folder_name=folder_name, files=files)


@app.route("/uploads/<folder_name>/<filename>")
def uploaded_file(folder_name, filename):
    safe_folder = secure_filename(folder_name)
    # Serve only from the uploads directory
    return send_from_directory(UPLOAD_ROOT / safe_folder, filename, as_attachment=False)

@app.route('/uploads/<path:filename>')
def serve_image(filename):
    return send_from_directory('uploads', filename)


@app.route("/download/<folder_name>/<filename>")
def download_file(folder_name, filename):
    safe_folder = secure_filename(folder_name)
    return send_from_directory(UPLOAD_ROOT / safe_folder, filename, as_attachment=True)


@app.route("/delete/<folder_name>/<filename>", methods=["POST"])
def delete_file(folder_name, filename):
    safe_folder = secure_filename(folder_name)
    path = UPLOAD_ROOT / safe_folder / filename
    if path.exists() and path.is_file():
        path.unlink()
        flash(f"Deleted {filename}", "info")
    else:
        flash("File not found", "warning")
    # Redirect back to the folder page
    try:
        folder_id = int(safe_folder.replace("folder", ""))
        return redirect(url_for("folder_view", folder_id=folder_id))
    except Exception:
        return redirect(url_for("index"))


if __name__ == "__main__":
    # development server
    app.run(host="0.0.0.0", port=5000, debug=True)
