from flask import Flask
import os 

app = Flask('')

@app.route('/')
def home():
    return "Bot is awake and running!"

def keep_alive():  
    # Gunicorn handles the running process, so we just run the bot.
    pass
