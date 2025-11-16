from flask import Flask
from threading import Thread
import os # <--- THIS LINE IS CRUCIAL

app = Flask('')

@app.route('/')
def home():
    return "Bot is awake and running!"

def run():
  # Get the PORT from the environment (where Railway puts it)
  port = int(os.environ.get('PORT', 8080))
  # Host MUST be 0.0.0.0 for external access/detection
  app.run(host='0.0.0.0', port=port)

def keep_alive():  
    t = Thread(target=run)
    t.start()
