from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    # Simple message to show the uptime monitor that the service is running
    return "Bot is awake and running!"

def run():
  # We bind to 0.0.0.0 and use a default port (8080)
  # Railway often sets the correct port automatically, but this is a reliable fallback
  app.run(host='0.0.0.0',port=8080)

def keep_alive():  
    # Run the web server in a separate thread so it doesn't block the Discord bot
    t = Thread(target=run)
    t.start()
