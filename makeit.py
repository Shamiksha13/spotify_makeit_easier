import os
from flask import Flask, session, redirect, request, url_for
import spotipy
from spotipy.oauth2 import SpotifyOAuth

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "default_secret_key")

CLIENT_ID = os.environ.get("CLIENT_ID")
CLIENT_SECRET = os.environ.get("CLIENT_SECRET")
REDIRECT_URI = os.environ.get("REDIRECT_URI")

SCOPE = "playlist-modify-public playlist-modify-private user-library-read user-read-email"

sp_oauth = SpotifyOAuth(client_id=CLIENT_ID,
                        client_secret=CLIENT_SECRET,
                        redirect_uri=REDIRECT_URI,
                        scope=SCOPE,
                        cache_path=".cache")


@app.route('/')
def login():
    auth_url = sp_oauth.get_authorize_url() + '&prompt=login'
    return f'''
    <html>
    <head>
      <style>
        body {{ font-family: Arial, sans-serif; background-color: #121212; color: white; text-align: center; padding: 50px; }}
        a.login-btn {{
          background-color: #1DB954; color: white; padding: 15px 30px; text-decoration: none; border-radius: 50px; font-weight: bold;
          font-size: 18px; display: inline-block; margin-top: 30px;
        }}
        a.login-btn:hover {{ background-color: #1ed760; }}
        h1 {{ font-size: 36px; margin-bottom: 10px; }}
      </style>
    </head>
    <body>
      <h1>Spotify Login</h1>
      <a class='login-btn' href="{auth_url}">Log in with Spotify</a>
    </body>
    </html>
    '''


@app.route('/callback')
def callback():
    code = request.args.get('code')
    token_info = sp_oauth.get_access_token(code)
    session['token_info'] = token_info
    return redirect(url_for('home'))


@app.route('/home')
def home():
    token_info = session.get('token_info', None)
    if not token_info:
        return redirect(url_for('login'))
    sp = spotipy.Spotify(auth=token_info['access_token'])
    user = sp.me()
    return f'''
    <html>
    <head>
      <style>
        body {{ font-family: Arial, sans-serif; background-color: #121212; color: white; text-align: center; padding: 50px; }}
        a.btn {{
          background-color: #1DB954; color: white; padding: 10px 20px; text-decoration: none; border-radius: 30px; font-weight: bold;
          font-size: 16px; display: inline-block; margin: 10px 5px;
        }}
        a.btn:hover {{ background-color: #1ed760; }}
        h1 {{ font-size: 32px; margin-bottom: 10px; }}
        p {{ font-size: 20px; }}
      </style>
    </head>
    <body>
      <h1>Welcome, {user['display_name']}!</h1>
      <p>User ID: {user['id']}</p>
      <a class='btn' href="/copy_songs">Copy Your Liked Songs</a>
      <a class='btn' href="/logout">Log out</a>
    </body>
    </html>
    '''


@app.route('/copy_songs')
def copy_songs():
    token_info = session.get('token_info', None)
    if not token_info:
        return redirect(url_for('login'))
    sp = spotipy.Spotify(auth=token_info['access_token'])
    user_id = sp.me()["id"]
    playlist = sp.user_playlist_create(user=user_id, name="Your Songs", public=False)
    playlist_id = playlist["id"]
    results = sp.current_user_saved_tracks(limit=50)
    songs = results["items"]
    while results['next']:
        results = sp.next(results)
        songs.extend(results["items"])
    track_uris = [item["track"]["uri"] for item in songs]
    for i in range(0, len(track_uris), 100):
        sp.playlist_add_items(playlist_id, track_uris[i:i + 100])
    return "✅ Playlist created successfully!"


@app.route('/logout')
def logout():
    session.clear()
    return '''
    <html>
    <head>
      <style>
        body {{ font-family: Arial, sans-serif; background-color: #121212; color: white; text-align: center; padding: 50px; }}
        a.btn {{
          background-color: #1DB954; color: white; padding: 10px 20px; text-decoration: none; border-radius: 30px; font-weight: bold;
          font-size: 16px; display: inline-block; margin: 10px 5px;
        }}
        a.btn:hover {{ background-color: #1ed760; }}
        h1 {{ font-size: 32px; margin-bottom: 10px; }}
      </style>
    </head>
    <body>
      <h1>You have been logged out.</
