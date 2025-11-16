from flask import Flask
from threading import Thread
import os 

app = Flask('')

@app.route('/')
def home():
    return "Bot is awake and running!"

def run():
  # This uses the dynamic port provided by Railway
  port = int(os.environ.get('PORT', 8080))
  app.run(host='0.0.0.0', port=port)

def keep_alive():  
    # Run the web server in a separate thread
    t = Thread(target=run)
    t.start()
