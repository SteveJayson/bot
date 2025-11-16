from flask import Flask
# NOTE: We remove Threading because gunicorn handles it.
import os 

app = Flask('')

@app.route('/')
def home():
    return "Bot is awake and running!"

def keep_alive():  
    # Gunicorn handles the running process, so we just run the bot.
    # The Flask app is started separately by the Procfile command.
    pass # No action needed here now, the bot runs in main.py
