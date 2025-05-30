import cv2
import numpy as np
import imutils
from imutils.perspective import four_point_transform

def preprocess_image(image):
    """Enhance image for OCR processing."""
    try:
        # Convert PIL image to numpy array if needed
        if isinstance(image, np.ndarray):
            img = image
        else:
            img = np.array(image)

        # Resize for processing
        resized = imutils.resize(img, width=1000)
        ratio = img.shape[1] / float(resized.shape[1])
        
        # Convert to grayscale
        gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
        
        # Denoising
        denoised = cv2.fastNlMeansDenoising(gray, h=10, templateWindowSize=7, searchWindowSize=21)
        
        # Adaptive thresholding
        thresh = cv2.adaptiveThreshold(
            denoised, 255, 
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 31, 10
        )
        
        # Perspective correction
        cnts = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cnts = imutils.grab_contours(cnts)
        cnts = sorted(cnts, key=cv2.contourArea, reverse=True)[:5]
        
        receiptCnt = None
        for c in cnts:
            peri = cv2.arcLength(c, True)
            approx = cv2.approxPolyDP(c, 0.02 * peri, True)
            if len(approx) == 4:
                receiptCnt = approx
                break
        
        if receiptCnt is not None:
            transformed = four_point_transform(img, receiptCnt.reshape(4, 2) * ratio)
        else:
            transformed = img

        return transformed

    except Exception as e:
        print(f"Preprocessing error: {str(e)}")
        return image