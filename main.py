from http.client import TOO_MANY_REQUESTS
import time
import tweepy
import json
import telegram

with open("config.json", "r") as f:
    settings = json.loads(f.read()) 

BEARER_TOKEN = settings.get("bearer_token")

USERNAMES = settings.get("usernames")
assert type(USERNAMES) == list, f"Expected usernames to be type list, got {type(USERNAMES)} instead!"

TELEGRAM_TOKEN = settings.get("telegram_token")
CHANNEL_ID = settings.get("channel_id")

WAIT_API = settings.get("wait_between_api_calls")

client = tweepy.Client(bearer_token=BEARER_TOKEN)

telegram_bot = telegram.Bot(token=TELEGRAM_TOKEN)


with open("./data/users.json", "r") as f:
    try:
        user_data = json.loads(f.read())
    except Exception as e:
        print(e)
        user_data = []

    current_users = []

    for username in USERNAMES:
        user_in_file = False
        for user in user_data:
            if username == user.get("username"):
                user_in_file = True
                current_users.append(user)
                break
        if not user_in_file:
            user_id = client.get_user(username=username).data["id"]
            current_users.append({
                "username": username,
                "id": user_id,
                "follows": []
            })
            user_data.append({
                "username": username,
                "id": user_id,
                "follows": []
            })

with open("./data/users.json", "w") as f:
    f.write(json.dumps(user_data, indent=4))

while True:
    try:
        for user in current_users:
            # Get last 10 follows of user
            follows = client.get_users_following(user["id"], max_results=10)
            
            if follows.data:
                
                new_follows = []
                
                #Go through follows
                for follow in follows.data:
                    #If a follow is already known break the loop, else append to new_follows
                    if follow.username in user.get("follows"):
                        break
                    
                    new_follows.append(follow.username)
                
                if new_follows:
                    
                    for dataset in user_data:
                        
                        if dataset.get("id") is user.get("id"):
                            [dataset.get('follows').append(new_follow) for new_follow in new_follows]
                            #write new follows in users.json
                            with open("./data/users.json", "w") as f:
                                f.write(json.dumps(user_data, indent=4))
                    
                    html_str = f"<b>NEW follow detected from: {user.get('username')}</b>\n"
                    for follow in new_follows:
                        html_str += f"{follow}: https://twitter.com/{follow}\n"
                    print(html_str)
                    telegram_bot.send_message(text=html_str, chat_id=CHANNEL_ID, parse_mode="html")
            
            time.sleep(WAIT_API)
    except tweepy.errors.TooManyRequests as e:
        print("Timeout Error, waiting 5min before trying again...")
        time.sleep(300)
    except Exception as e:
        print("Error in main loop", e)
