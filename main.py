import os

import discord
import cv2
import pytesseract
import image_preprocessing
import user
import pathlib
import logging
import logging.config
import boto3
from botocore.exceptions import ClientError
from datetime import datetime


TOKEN = os.getenv('DISCORD_TOKEN')

#Need this to retrieve members from server
intents = discord.Intents.all()
client = discord.Client(intents=intents)
cur_dir = pathlib.Path().absolute()

logging.basicConfig(filename='bot_logs.log', level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

dynamodb = boto3.resource('dynamodb', region_name='us-west-2')


#Current override of discord names to tarkov names until I implement a DB to remember it
discord_to_tarkov_name = {
    "deadfox0": "Hyakulol",
    "ZerO_0": "ArcZerO",
    "Pokguy604": "Pokguy",
    # Fucking Sheridan with his weirdass unicode discord name smh my head
    "{}{}".format(chr(734), chr(734)): "YunginCSTTV"
}


def tarkov_members():
    member_list = []
    for member in client.guilds[0].get_role(742241625727696957).members:
        if member.name in discord_to_tarkov_name:
            member_list.append(user.TarkovProfile(member, discord_to_tarkov_name[member.name]))
        else:
            member_list.append(user.TarkovProfile(member))
    return member_list

async def message_validation(message):
    if not client.user.mentioned_in(message):
        return
    if message.attachments is None:
        await message.channel.send("I can only understand images. Please upload an image of someone teamkilling you")
        return
    if len(message.attachments) > 1:
        await message.channel.send("Please only upload 1 image")
        return
    return message.attachments[0]

@client.event
async def on_ready():
    logger.info(f'{client.user} has connected to Discord!')
    print(f'{client.user} has connected to Discord!')

@client.event
async def on_message(message):

    if message.author == client.user:
        return
    if message.channel.name == "bot-testing" or message.channel.name == "turkov":
        validated_message = await message_validation(message)
        if validated_message is None:
            return
        
        member_list = tarkov_members()
        downloaded_img = await validated_message.save(str(cur_dir) + "/tmp/pic.png")
        img = cv2.imread(str(cur_dir) + "/tmp/pic.png")

        # upscale image for better OCR results
        scale_percent = 500 # percent of original size    
        resized = image_preprocessing.scale_image(img, scale_percent)

        # Grayscale then apply Otsu's threshold 
        # https://opencv-python-tutroals.readthedocs.io/en/latest/py_tutorials/py_imgproc/py_thresholding/py_thresholding.html#otsus-binarization
        gray = image_preprocessing.grayscale(resized)
        invertImg = cv2.bitwise_not(gray)
        thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]

        # Morph open to remove noise
        result = image_preprocessing.morph_open(thresh)

        logger.info("Image loaded successfully")
        # cv2.imshow('URL Image', invertImg)
        # cv2.waitKey()
        # Crazy how with all the image preprocessing simply upscaling then inverting it makes the most progress
        text = pytesseract.image_to_string(invertImg, lang='eng', config='--psm 11').casefold()

        # Algorithm to find who killed who
        # Definitely needs to be improved, this is just a non-scalable brute force solution
        killer_found = False
        killee_found = False
        for word in text.split(' '):
            for member in member_list:
                if member.tarkov_name.casefold() == word and not killer_found:
                    killer_found = True
                    killer = member.tarkov_name
                    killer_discord_id = member.discord_id
                elif member.tarkov_name.casefold() == word and killer_found:
                    killee_found = True
                    killee = member.tarkov_name
                    killee_discord_id = str(member.discord_id)
                    break
                else:
                    pass
            if killee_found:
                break
        confirmed_kill_text = "Confirmed: {} killed {}".format(killer, killee)
        logger.info(confirmed_kill_text)
        try:
            table = dynamodb.Table(str(killer_discord_id))
            table.put_item(
                Item={
                    'time': datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                    'discord_id': killee_discord_id,
                    'tarkov_name': killee
                }
            )
        except ClientError as e:
            logger.error(e.response['Error']['Message'])
        except Exception as e:
            logger.error(e)
        await message.channel.send(confirmed_kill_text)


client.run(TOKEN)


