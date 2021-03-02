import glob 
import re

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

for image in images: 
    text_results = " " # Needs Modularized Image processing function here
    result = re.findall(username_filter, text_results, filter=re.IGNORECASE)
    truth = get_killer_and_killee(image)
    if (len(result) == 2 and result[0] == truth[0] and result[1] == truth[1]): 
        print("{} - PASSED".format(image.split('/')[-1])) 
    else: 
        print("{} - FAILED".format(image.split('/')[-1])) 
