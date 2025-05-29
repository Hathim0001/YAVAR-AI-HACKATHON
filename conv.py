from PIL import Image
import os

input_dir = "input_pdfs/train/"
output_dir = "op/"
os.makedirs(output_dir, exist_ok=True)

for filename in os.listdir(input_dir):
    if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
        img_path = os.path.join(input_dir, filename)
        img = Image.open(img_path).convert('RGB')
        pdf_filename = os.path.splitext(filename)[0] + ".pdf"
        pdf_path = os.path.join(output_dir, pdf_filename)
        img.save(pdf_path)
        print(f"Converted {filename} to {pdf_filename}")
