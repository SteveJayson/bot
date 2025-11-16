from flask import Flask
from threading import Thread
import os # ⚠️ Necessary to read the PORT variable

app = Flask('')

@app.route('/')
def home():
    return "Bot is awake and running!"

def run():
  # Get the PORT from the environment (defaulting to 8080)
  port = int(os.environ.get('PORT', 8080))
  # The host MUST be 0.0.0.0 for external access/detection
  app.run(host='0.0.0.0', port=port)

def keep_alive():  
    # Run the web server in a separate thread so it doesn't block the Discord bot
    t = Thread(target=run)
    t.start()
