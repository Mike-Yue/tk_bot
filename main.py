import os

import discord
import cv2
import pytesseract
import re
import image_preprocessing
import user
import pathlib
import logging
import logging.config
import boto3
import sys
import numpy as np
from botocore.exceptions import ClientError
from datetime import datetime
from dotenv import load_dotenv, find_dotenv
import pandas as pd

load_dotenv(find_dotenv())
TOKEN = os.getenv('DISCORD_TOKEN')

#Need this to retrieve members from server
intents = discord.Intents.all()
client = discord.Client(intents=intents)
cur_dir = pathlib.Path().absolute()

logging.basicConfig(filename='bot_logs.log', level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

if len(sys.argv) == 1:
    dynamodb = boto3.resource('dynamodb', region_name='us-west-2')
elif sys.argv[1] == "test":
    dynamodb = boto3.resource('dynamodb', endpoint_url="http://localhost:8000", region_name='us-west-2')
else:
    sys.exit("Invalid command line arg provided")


def tarkov_members():
    member_list = []
    table = dynamodb.Table("DiscordToTarkovName")
    for member in client.guilds[0].get_role(742241625727696957).members:
        try:
            response = table.get_item(Key={'discord_id': str(member.id)})
            tarkov_name = response['Item']['tarkov_name'].lower()
            logger.info("Pulled tarkov username {} for discord user {}".format(tarkov_name, member.name))
        except ClientError as e:
            logger.error(e.response['Error']['Message'])
            tarkov_name = member.name
        member_list.append(user.TarkovProfile(member, tarkov_name))
    return member_list

def message_validation(message):
    print(message.content)
    if not client.user.mentioned_in(message):
        return
    if len(message.attachments) == 0 and "!showstats" in message.content:
        return "!showstats"
    if len(message.attachments) == 1:
        return "teamkill"
    if len(message.attachments) > 1:
        return "error"
    return "error"

    

@client.event
async def on_ready():
    logger.info(f'{client.user} has connected to Discord!')
    print(f'{client.user} has connected to Discord!')

@client.event
async def on_message(message):

    if message.author == client.user:
        return
    if message.channel.name == "bot-testing" or message.channel.name == "turkov":
        validated_message = message_validation(message)
        if validated_message == "Error":
            await message.channel.send("I didn't understand what you want to do. Please retry")
            return
        elif validated_message == "!showstats":
            stats_dict = {}
            for member in client.guilds[0].get_role(742241625727696957).members:
                table = dynamodb.Table(str(member.id))
                try:
                    data = table.scan()
                    stats_dict[member.name] = data['Count']
                except ClientError as e:
                    logger.error(e.response['Error']['Message'])

            df = pd.DataFrame.from_dict(stats_dict, orient='index', columns=["Team Kill Count"])
            await message.channel.send(df.to_markdown(tablefmt="grid"))
        elif validated_message == "teamkill":
            member_dict = {member.tarkov_name: member for member in tarkov_members()}

            downloaded_img = await message.attachments[0].save(str(cur_dir) + "/tmp/pic.png")
            img = cv2.imread(str(cur_dir) + "/tmp/pic.png")
            logger.info("Image loaded successfully")

            # Preprocess image for increased accuracy
            processed = image_preprocessing.preprocess(img)

            # Save image for viewing purposes
            cv2.imwrite(str(cur_dir) + "/tmp/processed.png", processed)

            text = pytesseract.image_to_string(processed, lang='eng').casefold()
            logger.info("{}: {}".format("Image to text dump", text))

            username_filter = '|'.join(member_dict.keys())

            names = re.findall(username_filter, text, flags=re.IGNORECASE)

            if (len(names) == 2):  # [killer.tarkov_name, killee.tarkov_name]
                confirmed_kill_text = "Confirmed: {} killed {}".format(names[0], names[1])
                logger.info(confirmed_kill_text)
                if message.channel.name == "turkov":
                    try:
                        table = dynamodb.Table(str(member_dict[names[0]].discord_id))
                        table.put_item(
                            Item={
                                'time': datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                                'discord_id': member_dict[names[1]].discord_id, #Killee.discord_id 
                                'tarkov_name': names[1] #Killee.tarkov_name
                            }
                        )
                    except ClientError as e:
                        logger.error(e.response['Error']['Message'])
                    except Exception as e:
                        logger.error(e)
                await message.channel.send(confirmed_kill_text)

client.run(TOKEN)


