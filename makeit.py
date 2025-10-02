import os
from flask import Flask, session, redirect, request, url_for, render_template
import spotipy
from spotipy.oauth2 import SpotifyOAuth

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "default_secret_key")

CLIENT_ID = os.environ.get("CLIENT_ID")
CLIENT_SECRET = os.environ.get("CLIENT_SECRET")
REDIRECT_URI = os.environ.get("REDIRECT_URI")

SCOPE = "playlist-modify-public playlist-modify-private user-library-read user-read-email"

sp_oauth = SpotifyOAuth(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    redirect_uri=REDIRECT_URI,
    scope=SCOPE,
    cache_path=".cache",
    show_dialog=True
)


@app.route('/')
def login():
    auth_url = sp_oauth.get_authorize_url()
    return render_template('login.html', auth_url=auth_url)


@app.route('/callback')
def callback():
    code = request.args.get('code')
    if code:
        token_info = sp_oauth.get_access_token(code, as_dict=True)  # ✅ fixed
        session['token_info'] = token_info
        return redirect(url_for('home'))
    else:
        return "Error: No code provided by Spotify", 400


@app.route('/home')
def home():
    token_info = session.get('token_info')
    if not token_info:
        return redirect(url_for('login'))

    sp = spotipy.Spotify(auth=token_info['acc]()_
