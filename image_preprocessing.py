import cv2
import pytesseract
import logging
import platform

logger = logging.getLogger(__name__)

if platform.system() == 'Windows':
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def grayscale(image):
    logger.info('Grayscaling image')
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

def blur(image):
    return cv2.GaussianBlur(image,(5,5),0)

def scale_image(image, scale_percent):
    width = int(image.shape[1] * scale_percent / 100)
    height = int(image.shape[0] * scale_percent / 100)
    dim = (width, height)
      
    # resize image
    resized = cv2.resize(image, dim, interpolation = cv2.INTER_AREA)
    return resized

def morph_open(image):
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2,2))
    opening = cv2.morphologyEx(image, cv2.MORPH_OPEN, kernel, iterations=1)
    cnts = cv2.findContours(opening, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnts = cnts[0] if len(cnts) == 2 else cnts[1]
    for c in cnts:
        area = cv2.contourArea(c)
        if area < 50:
            cv2.drawContours(opening, [c], -1, 0, -1)

    # Invert and apply slight Gaussian blur
    result = 255 - opening
    result = cv2.GaussianBlur(result, (3,3), 0)
    return result

# Contrast Limited Adaptive Histogram Equalization
def clahe(image):
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    clahe_bgr = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
    grayimg1 = cv2.cvtColor(clahe_bgr, cv2.COLOR_BGR2GRAY)
    mask2 = cv2.threshold(grayimg1 , 220, 255, cv2.THRESH_BINARY)[1]
    result2 = cv2.inpaint(image, mask2, 0.1, cv2.INPAINT_TELEA)
    return result2

# Applies a series of filters to enhance OCR accuracy
def preprocess(image):
    # upscale image for better OCR results
    scale_percent = 500 # percent of original size    
    resized = scale_image(image, scale_percent)
    # equalize image to reduce glare and glow
    equalized = clahe(resized)
    # grayscale image
    gray = grayscale(equalized)
    # invert image
    invertImg = cv2.bitwise_not(gray)
    return invertImg

# Grayscale then apply Otsu's threshold 
# https://opencv-python-tutroals.readthedocs.io/en/latest/py_tutorials/py_imgproc/py_thresholding/py_thresholding.html#otsus-binarization
# thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]

    # # Morph open to remove noise
    # result = image_preprocessing.morph_open(thresh)
