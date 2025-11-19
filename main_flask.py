import os
import time
from flask import Flask, request, jsonify, send_from_directory, abort
from werkzeug.utils import secure_filename

# Import from image_ops
from image_ops import (
    open_image_from_bytes,
    save_bytes_to_file,
    resize_image,
    crop_image,
    change_aspect_ratio,
    convert_and_save,
    generate_thumbnail,
    rotate_image   
)

# Directories
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
PROC_DIR = os.path.join(BASE_DIR, "processed")

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(PROC_DIR, exist_ok=True)

app = Flask(__name__)


# Defines a root endpoint
@app.route("/")
def root():
    return jsonify({"status": "ok", "framework": "flask"})


# Defines an endpoint at upload
@app.route("/upload", methods=["POST"])
def upload_image():
    if "file" not in request.files:
        return jsonify({"detail": "file required"}), 400

    f = request.files["file"]
    if f.filename == "":
        return jsonify({"detail": "empty filename"}), 400

    safe_name = secure_filename(f.filename)
    content = f.read()

    filename = f"{int(time.time())}_{safe_name}"
    path = os.path.join(UPLOAD_DIR, filename)

    save_bytes_to_file(content, path)

    return jsonify({"filename": filename, "path": path})


# ---------------------
# RESIZE
# ---------------------
@app.route("/resize", methods=["POST"])
def resize():
    filename = request.form.get("filename")
    if not filename:
        return jsonify({"detail": "filename required"}), 400

    try:
        width = int(request.form.get("width")) if request.form.get("width") else None
        height = int(request.form.get("height")) if request.form.get("height") else None
    except:
        return jsonify({"detail": "width/height must be integers"}), 400

    keep_aspect = request.form.get("keep_aspect", "true").lower() not in ("0","false","no")

    src = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(src):
        return jsonify({"detail": "file not found"}), 404

    with open(src, "rb") as f:
        img = open_image_from_bytes(f.read())

    out = resize_image(img, width=width, height=height, keep_aspect=keep_aspect)

    out_name = f"resized_{filename}"
    out_path = os.path.join(PROC_DIR, out_name)

    convert_and_save(out, out_path, fmt="JPEG", quality=85)

    return jsonify({"processed": out_name, "path": out_path})


# ---------------------
# CROP
# ---------------------
@app.route("/crop", methods=["POST"])
def crop():
    filename = request.form.get("filename")
    if not filename:
        return jsonify({"detail": "filename required"}), 400

    try:
        left = int(request.form.get("left"))
        upper = int(request.form.get("upper"))
        right = int(request.form.get("right"))
        lower = int(request.form.get("lower"))
    except:
        return jsonify({"detail": "coordinates must be integers"}), 400

    src = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(src):
        return jsonify({"detail": "file not found"}), 404

    with open(src, "rb") as f:
        img = open_image_from_bytes(f.read())

    out = crop_image(img, left, upper, right, lower)

    out_name = f"crop_{filename}"
    out_path = os.path.join(PROC_DIR, out_name)

    convert_and_save(out, out_path, fmt="JPEG", quality=90)

    return jsonify({"processed": out_name, "path": out_path})


# ---------------------
# CHANGE ASPECT RATIO
# ---------------------
@app.route("/aspect", methods=["POST"])
def aspect():
    filename = request.form.get("filename")
    if not filename:
        return jsonify({"detail": "filename required"}), 400

    try:
        target_w = int(request.form.get("target_w"))
        target_h = int(request.form.get("target_h"))
    except:
        return jsonify({"detail": "target_w and target_h must be integers"}), 400

    mode = request.form.get("mode", "fit")

    src = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(src):
        return jsonify({"detail": "file not found"}), 404

    with open(src, "rb") as f:
        img = open_image_from_bytes(f.read())

    out = change_aspect_ratio(img, target_w, target_h, mode=mode)

    out_name = f"aspect_{mode}_{filename}"
    out_path = os.path.join(PROC_DIR, out_name)

    convert_and_save(out, out_path, fmt="JPEG", quality=90)

    return jsonify({"processed": out_name, "path": out_path})


# creates an endpoint at convert
@app.route("/convert", methods=["POST"])
def convert():
    filename = request.form.get("filename")
    if not filename:
        return jsonify({"detail": "filename required"}), 400

    fmt = request.form.get("fmt", "JPEG")
    quality = int(request.form.get("quality", 85))

    src = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(src):
        return jsonify({"detail": "file not found"}), 404

    with open(src, "rb") as f:
        img = open_image_from_bytes(f.read())

    name_root, _ = os.path.splitext(filename)
    out_name = f"{name_root}.{fmt.lower()}"
    out_path = os.path.join(PROC_DIR, out_name)

    convert_and_save(img, out_path, fmt=fmt, quality=quality)

    return jsonify({"processed": out_name, "path": out_path})


# ---------------------
# THUMBNAIL
# ---------------------
@app.route("/thumbnail", methods=["POST"])
def thumbnail():
    filename = request.form.get("filename")
    if not filename:
        return jsonify({"detail": "filename required"}), 400

    w = int(request.form.get("w", 200))
    h = int(request.form.get("h", 200))

    src = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(src):
        return jsonify({"detail": "file not found"}), 404

    with open(src, "rb") as f:
        img = open_image_from_bytes(f.read())

    thumb = generate_thumbnail(img, size=(w, h))

    out_name = f"thumb_{filename}"
    out_path = os.path.join(PROC_DIR, out_name)

    convert_and_save(thumb, out_path, fmt="JPEG", quality=80)

    return jsonify({"thumbnail": out_name, "path": out_path})


# ---------------------
# ROTATE
# ---------------------
@app.route("/rotate", methods=["POST"])
def rotate():
    filename = request.form.get("filename")
    if not filename:
        return jsonify({"detail": "filename required"}), 400

    try:
        angle = int(request.form.get("angle"))
    except:
        return jsonify({"detail": "angle must be an integer"}), 400

    expand = request.form.get("expand", "true").lower() not in ("0", "false", "no")

    src = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(src):
        return jsonify({"detail": "file not found"}), 404

    with open(src, "rb") as f:
        img = open_image_from_bytes(f.read())

    out = rotate_image(img, angle=angle, expand=expand)

    out_name = f"rotate_{angle}_{filename}"
    out_path = os.path.join(PROC_DIR, out_name)

    convert_and_save(out, out_path, fmt="JPEG", quality=90)

    return jsonify({"processed": out_name, "path": out_path})


# ---------------------
# DOWNLOAD
# ---------------------
@app.route("/download/<kind>/<fname>", methods=["GET"])
def download(kind, fname):
    if kind not in ("uploads", "processed"):
        return jsonify({"detail": "invalid kind"}), 400

    directory = UPLOAD_DIR if kind == "uploads" else PROC_DIR
    file_path = os.path.join(directory, fname)

    if not os.path.exists(file_path):
        return jsonify({"detail": "file not found"}), 404

    return send_from_directory(directory, fname, as_attachment=True)


# ---------------------
# RUN SERVER
# ---------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)