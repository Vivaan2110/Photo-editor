from PIL import Image, ImageOps, ImageEnhance
from io import BytesIO
import os

os.makedirs("uploads", exist_ok=True)
os.makedirs("processed", exist_ok=True)

def save_bytes_to_file(b: bytes, dest_path: str):
    with open(dest_path, "wb") as f:  # Opens the file in write binary mode
        f.write(b) # Writes the image to the file

def open_image_from_bytes(b: bytes) -> Image.Image: # Returns a PIL image
    return Image.open(BytesIO(b)) # Converts the bytes from memory to an image file

# Inputs the image, new width, new height
def resize_image(img: Image.Image, width: int = None, height: int = None, keep_aspect=True):
    if not width and not height: # If width and height are NULL
        return img
    if keep_aspect:
        # Use provided width or height, else keep it the same the same
        img.thumbnail((width or img.width, height or img.height), Image.LANCZOS) # .thumbnail keeps the aspect ratio
        return img
    # Runs if keep_aspect is set to false
    return img.resize((width or img.width, height or img.height), Image.LANCZOS) # LANCZOS allows for high quality image resizing

# Takes in x-coordinate of the left and right side and y-coordinate of the upper and lower side
def crop_image(img: Image.Image, left:int, upper:int, right:int, lower:int):
    return img.crop((left, upper, right, lower)) # Cuts a box using the given x and y cooridnates 

# Takes in the image, target width, target height, the mode(default=fill) and background color for padding(default=white)
def change_aspect_ratio(img: Image.Image, target_w:int, target_h:int, mode="fit", fill_color=(255,255,255)):
    
    # Fit mode makes the image fit inside the given width and height without any cropping and resizing
    if mode == "fit":
        img_c = ImageOps.contain(img, (target_w, target_h), Image.LANCZOS) # Returns a resized image that fits inside the given aspect ratio but might have white spaces
        background = Image.new("RGB", (target_w, target_h), fill_color) # Creates a blank canvas with target width and height
        offset = ((target_w - img_c.width)//2, (target_h - img_c.height)//2) # Calculates the center position to paste the image
        background.paste(img_c, offset) # Pastes the image at the center
        return background
    
    # Fill means resize the image till the box is filled and then crop the rest
    elif mode == "fill":
        return ImageOps.fit(img, (target_w, target_h), Image.LANCZOS, centering=(0.5,0.5)) # centering tells where to keep the image
    
    # Resize the image by adding padding 
    elif mode == "pad":
        return ImageOps.pad(img, (target_w, target_h), color=fill_color) # Uses the given fill_color to fill the extra spaces
    else:
        raise ValueError("unknown mode")

# Converts an image to a given format, saves it to memory and can change the quality
def convert_and_save(img: Image.Image, out_path: str, fmt: str = "JPEG", quality: int = 85, optimize=True):
    save_params = {}
    if fmt.upper() == "JPEG":
        
        # If the image has an alpha value, it must be removed as it cannot be saved by JPEG
        if img.mode in ("RGBA","LA"):
            bg = Image.new("RGB", img.size, (255,255,255)) # Creates a new image with a white background with the same size
            bg.paste(img, mask=img.split()[-1]) # Splits the image into RGBA channels and only pastes when alpha channel is visible
            img = bg
        elif img.mode != "RGB":
            img = img.convert("RGB") # Comverts the mode to RGB
        save_params.update({"format":"JPEG", "quality":quality, "optimize": optimize}) # Updates the saved parameters for the JPEG specific file
    # If not a JPEG, specify the formay by the user
    else:
        save_params.update({"format": fmt.upper()})
    img.save(out_path, **save_params) # Save the image to the disk using the specified format
    return out_path

# Can create a thumbnail version of the image with a max size of 200x200
def generate_thumbnail(img: Image.Image, size=(200,200)):
    thumb = img.copy() # Creates a copy of the image
    thumb.thumbnail(size, Image.LANCZOS) # Resizes it according to teh given size
    return thumb