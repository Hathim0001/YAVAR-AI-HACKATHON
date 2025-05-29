from PIL import Image

# Load your image
image = Image.open("D:/YAVAR-AI-HACKATHON/pdfs/samples/11574341.jpg")

# Convert to RGB if not already
if image.mode != 'RGB':
    image = image.convert('RGB')

# Save as PDF
image.save("invsam.pdf")
