import os
from PIL import Image, ImageOps

def process_image(img_path):
    try:
        with Image.open(img_path) as img:
            # 1. 修正 EXIF 方向
            img = ImageOps.exif_transpose(img)

            ext = os.path.splitext(img_path)[1].lower()

            # 2. 根据格式处理
            if ext in [".jpg", ".jpeg"]:
                # JPG：统一 RGB，去 EXIF
                if img.mode != "RGB":
                    img = img.convert("RGB")
                img.save(
                    img_path,
                    format="JPEG",
                    quality=95,
                    subsampling=0
                )
            elif ext == ".png":
                # PNG：保留格式，不写 EXIF
                img.save(img_path, format="PNG")
            else:
                return

            print(f"[OK] {img_path}")

    except Exception as e:
        print(f"[FAIL] {img_path} -> {e}")


def process_dir(root_dir):
    for root, _, files in os.walk(root_dir):
        for name in files:
            if name.lower().endswith((".jpg", ".jpeg", ".png")):
                process_image(os.path.join(root, name))


if __name__ == "__main__":
    IMAGE_DIR = r"D:\vehicle_compliance_2" 
    process_dir(IMAGE_DIR)