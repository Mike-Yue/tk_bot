# Discord Bot to track teamkills in Tarkov

Currently a WIP and a lot of code is rudimentary

## Setup
Create your own python 3 virtual env, and then run `pip install -r requirements.txt` to install required dependencies.

Message me to ask for the discord token, I'll have to come up with a better way to share the discord token in the future

## Future Goals
1: Host on an AWS server so it's up 24/7

2: Connect to a DB (probably Postgres?) so that data is persisted even when bot is offline

3: Improve image processing so that OCR can recognize screenshot text better

4: Detect when users in the Turkov Channel change their display names -> automatically update DB to reassociate their tarkov name with their new discord name

5: Ask users to confirm via text who TK-ed who if screenshot is unable to be parsed

6: Detect when new users get the PMC role in the server and automatically add them to the list of users to be considered when TK screenshots are submitted

7: Cache list of PMC members...currently the list is refreshed everytime the bot is mentioned, which is inefficient as the list doesn't change often

And many more that I probably forgot to mention here
