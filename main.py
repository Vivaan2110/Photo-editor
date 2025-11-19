from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
import os, time
from .image_ops import open_image_from_bytes, save_bytes_to_file, resize_image, crop_image, change_aspect_ratio, convert_and_save, generate_thumbnail

app = FastAPI(title="Photo Editor MVP")

UPLOAD_DIR = "uploads"
PROC_DIR = "processed"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(PROC_DIR, exist_ok=True)

@app.post("/upload")
async def upload_image(file: UploadFile = File(...)):
    content = await file.read()
    filename = f"{int(time.time())}_{os.path.basename(file.filename)}"
    path = os.path.join(UPLOAD_DIR, filename)
    save_bytes_to_file(content, path)
    return {"filename": filename, "path": path}

@app.post("/resize")
async def resize(filename: str = Form(...), width: int = Form(None), height: int = Form(None), keep_aspect: bool = Form(True)):
    src = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(src): raise HTTPException(404, "file not found")
    with open(src, "rb") as f:
        img = open_image_from_bytes(f.read())
    out = resize_image(img, width=width, height=height, keep_aspect=keep_aspect)
    out_name = f"resized_{filename}"
    out_path = os.path.join(PROC_DIR, out_name)
    convert_and_save(out, out_path, fmt="JPEG", quality=85)
    return {"processed": out_name, "path": out_path}

@app.post("/crop")
async def crop(filename: str = Form(...), left: int = Form(...), upper: int = Form(...), right: int = Form(...), lower: int = Form(...)):
    src = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(src): raise HTTPException(404, "file not found")
    with open(src, "rb") as f:
        img = open_image_from_bytes(f.read())
    out = crop_image(img, left, upper, right, lower)
    out_name = f"crop_{filename}"
    out_path = os.path.join(PROC_DIR, out_name)
    convert_and_save(out, out_path, fmt="JPEG", quality=90)
    return {"processed": out_name, "path": out_path}

@app.post("/aspect")
async def aspect(filename: str = Form(...), target_w: int = Form(...), target_h: int = Form(...), mode: str = Form("fit")):
    src = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(src): raise HTTPException(404, "file not found")
    with open(src, "rb") as f:
        img = open_image_from_bytes(f.read())
    out = change_aspect_ratio(img, target_w, target_h, mode=mode)
    out_name = f"aspect_{mode}_{filename}"
    out_path = os.path.join(PROC_DIR, out_name)
    convert_and_save(out, out_path, fmt="JPEG", quality=90)
    return {"processed": out_name, "path": out_path}

@app.post("/convert")
async def convert(filename: str = Form(...), fmt: str = Form("JPEG"), quality: int = Form(85)):
    src = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(src): raise HTTPException(404, "file not found")
    with open(src, "rb") as f:
        img = open_image_from_bytes(f.read())
    name_root, _ = os.path.splitext(filename)
    out_name = f"{name_root}.{fmt.lower()}"
    out_path = os.path.join(PROC_DIR, out_name)
    convert_and_save(img, out_path, fmt=fmt, quality=quality)
    return {"processed": out_name, "path": out_path}

@app.get("/download/{kind}/{fname}")
def download(kind: str, fname: str):
    if kind not in ("uploads","processed"): raise HTTPException(400)
    path = os.path.join(kind, fname)
    if not os.path.exists(path): raise HTTPException(404)
    return FileResponse(path, media_type="application/octet-stream", filename=fname)

@app.post("/thumbnail")
async def thumbnail(filename: str = Form(...), w: int = Form(200), h: int = Form(200)):
    src = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(src): raise HTTPException(404)
    with open(src, "rb") as f:
        img = open_image_from_bytes(f.read())
    thumb = generate_thumbnail(img, size=(w,h))
    out_name = f"thumb_{filename}"
    out_path = os.path.join(PROC_DIR, out_name)
    convert_and_save(thumb, out_path, fmt="JPEG", quality=80)
    return {"thumbnail": out_name, "path": out_path}