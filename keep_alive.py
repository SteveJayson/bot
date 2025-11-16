from flask import Flask
from threading import Thread
import os # ⚠️ Added os import to read environment variables

app = Flask('')

@app.route('/')
def home():
    return "Bot is awake and running!"

def run():
  # ⚠️ Railway often provides the port via the $PORT environment variable.
  # We read it here, defaulting to 8080 if not found (though 8080 is often used by Railway as a default)
  port = int(os.environ.get('PORT', 8080))
  # The host MUST be 0.0.0.0 for external access/detection
  app.run(host='0.0.0.0', port=port)

def keep_alive():  
    # Run the web server in a separate thread so it doesn't block the Discord bot
    t = Thread(target=run)
    t.start()
