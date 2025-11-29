from PIL import Image, ImageOps, ImageChops
import os

# Source image path
src_path = r"C:/Users/R2401-022/.gemini/antigravity/brain/0abacb67-2b85-47e0-b2bf-90d09d0306d7/zoomed_ruler_icon_1764378900395.png"
# Destination path
dst_path = r"c:/Users/R2401-022/Desktop/rpa/AI_dep/Gemini/Monosashi/icon.ico"

try:
    img = Image.open(src_path)
    img = img.convert("RGBA")
    
    # Trim whitespace
    bg = Image.new(img.mode, img.size, img.getpixel((0,0)))
    diff = ImageChops.difference(img, bg)
    diff = ImageChops.add(diff, diff, 2.0, -100)
    bbox = diff.getbbox()
    
    if bbox:
        img_cropped = img.crop(bbox)
    else:
        img_cropped = img
        
    # Resize to maximize usage of the square area
    icon_size = 256
    
    # Calculate new size maintaining aspect ratio to fit within icon_size x icon_size
    ratio = min(icon_size / img_cropped.width, icon_size / img_cropped.height)
    new_size = (int(img_cropped.width * ratio), int(img_cropped.height * ratio))
    img_resized = img_cropped.resize(new_size, Image.Resampling.LANCZOS)
    
    # Create a square canvas
    square_img = Image.new("RGBA", (icon_size, icon_size), (255, 255, 255, 0)) # Transparent background
    
    # Paste resized image in center
    offset = ((icon_size - new_size[0]) // 2, (icon_size - new_size[1]) // 2)
    square_img.paste(img_resized, offset)
    
    # Save as ICO
    square_img.save(dst_path, format='ICO', sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)])
    print(f"Successfully converted and cropped {src_path} to {dst_path}")
    
except Exception as e:
    print(f"Error converting image: {e}")
