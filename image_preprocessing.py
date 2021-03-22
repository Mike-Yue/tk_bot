import cv2
import pytesseract
import logging
import platform
import numpy as np

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

# Crop Image to only contain the names
# Yea I realize I hardcored a bunch of magic numbers bite me I'm desparate at this point
# Basically I assume the name is always near the center bottom of the screen so I crop towards there
def crop(image):
    height, width = image.shape[:2]
    start_y = int(height*0.53)
    end_y = int(height*0.58)
    start_x = int(width*0.2)
    end_x = width - start_x
    cropped = image[start_y:end_y, start_x:end_x]
    return cropped

def sharpen(image):
    # http://datahacker.rs/004-how-to-smooth-and-sharpen-an-image-in-opencv/
    sharpen_array = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]])
    return cv2.filter2D(image, -1, sharpen_array)

def Otsu(image):
    ret3, img = cv2.threshold(image, 0, 255,cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return img

# Applies a series of filters to enhance OCR accuracy
def preprocess(image):
    cropped = crop(image)
    # upscale image for better OCR results
    scale_percent = 200 # percent of original size    
    resized = scale_image(cropped, scale_percent)
    # equalize image to reduce glare and glow
    equalized = clahe(resized)
    # grayscale image
    gray = grayscale(equalized)

    blurred_img = blur(gray)
    sharpened_img = sharpen(blurred_img)
    otsu_img = Otsu(sharpened_img)

    # OpenCV stores images as BGR by default and Pytessract uses RGB
    img_rgb = cv2.cvtColor(otsu_img, cv2.COLOR_BGR2RGB)

    return img_rgb

