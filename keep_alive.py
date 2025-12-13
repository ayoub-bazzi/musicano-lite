from flask import Flask
from threading import Thread
import os

app = Flask('')

@app.route('/')
def home():
    return "I am alive!"

def run():
    # Render assigns a random port in the 'PORT' environment variable.
    # We default to 8080 if running locally.
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()