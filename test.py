import glob 
import re
import cv2
import image_preprocessing
import pytesseract

def get_killer_and_killee(image_path):
    killer_and_killee = image_path.split('/')[2].split('.')[0]
    return killer_and_killee.split(' ')


def build_usernames(image_paths):
    usernames = set()
    for image in image_paths:
        for name in get_killer_and_killee(image):
            usernames.add(name)
    return usernames


images = glob.glob('./test/*')
username_filter = '|'.join(build_usernames(images))

for image_path in images: 
    image = cv2.imread(image_path)
    image = image_preprocessing.preprocess(image)
    text_results = pytesseract.image_to_string(image, lang='eng', config='--psm 11').casefold()
    result = re.findall(username_filter, text_results, flags=re.IGNORECASE)


    truth = get_killer_and_killee(image_path)
    if (len(result) == 2 and result[0] == truth[0] and result[1] == truth[1]): 
        print("\x1b[6;30;42m" + "{} - PASSED".format(image_path.split('/')[-1]) + "\x1b[0m") 
    else: 
        print("\x1b[0;30;41m" + "{} - FAILED".format(image_path.split('/')[-1]) + "\x1b[0m")
        print("\x1b[0;30;41m" + "Raw results: \n {}".format(text_results) + "\x1b[0m")
