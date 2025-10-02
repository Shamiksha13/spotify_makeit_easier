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

sp_oauth = SpotifyOAuth(client_id=CLIENT_ID,
                        client_secret=CLIENT_SECRET,
                        redirect_uri=REDIRECT_URI,
                        scope=SCOPE,
                        cache_path=".cache")


@app.route('/')
def login():
    base_auth_url = sp_oauth.get_authorize_url()
    auth_url = base_auth_url + '&prompt=login'  # Force login every time
    return render_template('login.html', auth_url=auth_url)


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
    return render_template('home.html', user=user)


@app.route('/copy_songs')
def copy_songs():
    token_info = session.get('token_info', None)
    if not token_info:
        return redirect(url_for('login'))
    sp = spotipy.Spotify(auth=token_info['access_token'])
    user_id = sp.me()["id"]
    playlist = sp.user_playlist_create(user=user_id, name="your songs", public=False)
    playlist_id = playlist["id"]
    results = sp.current_user_saved_tracks(limit=50)
    songs = results["items"]
    while results["next"]:
        results = sp.next(results)
        songs.extend(results["items"])
    track_uris = [item["track"]["uri"] for item in songs]
    for i in range(0, len(track_uris), 100):
        sp.playlist_add_items(playlist_id, track_uris[i:i + 100])
    return "✅ Playlist created successfully!"


@app.route('/logout')
def logout():
    session.clear()
    return redirect("https://accounts.spotify.com/logout")


if __name__ == '__main__':
    app.run(port=8888, debug=True)

