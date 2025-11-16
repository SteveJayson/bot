from flask import Flask
from threading import Thread
import os 

# We define the Flask application object 'app' here, which Gunicorn will look for.
app = Flask('')

@app.route('/')
def home():
    return "Bot is awake and running!"

def run():
  # This function is now only used when the bot is run locally for testing.
  # On Railway, the Procfile uses Gunicorn to start 'app', bypassing this function.
  port = int(os.environ.get('PORT', 8080))
  app.run(host='0.0.0.0', port=port)

def keep_alive():  
    # Run the web server in a separate thread for local testing or simple hosting.
    t = Thread(target=run)
    t.start()
