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
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>Spotify Login</title>
  <style>
    body {{
      background-color: #121212;
      color: #1DB954;
      font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
      display: flex;
      justify-content: center;
      align-items: center;
      height: 100vh;
      margin: 0;
      flex-direction: column;
    }}
    h1 {{
      font-size: 3rem;
      margin-bottom: 2rem;
    }}
    a {{
      display: inline-block;
      padding: 15px 30px;
      font-size: 1.25rem;
      color: white;
      background-color: #1DB954;
      border-radius: 50px;
      text-decoration: none;
      transition: background-color 0.3s ease;
    }}
    a:hover {{
      background-color: #17a347;
    }}
  </style>
</head>
<body>
  <h1>Login to Spotify</h1>
  <a href="{auth_url}">Login with Spotify</a>
</body>
</html>'''

@app.route('/callback')
def callback():
    code = request.args.get('code')
    if code:
        token_info = sp_oauth.get_access_token(code, as_dict=True)
        session['token_info'] = token_info
        return redirect(url_for('home'))
    else:
        return "Error: No code provided by Spotify", 400

@app.route('/home')
def home():
    token_info = session.get('token_info')
    if not token_info:
        return redirect(url_for('login'))

    sp = spotipy.Spotify(auth=token_info['access_token'])
    user = sp.me()
    display_name = user.get('display_name', 'Unknown')
    user_id = user.get('id', 'Unknown')
    email = user.get('email') if user.get('email') else "Not available"
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>Welcome, {display_name}</title>
  <style>
    body {{
      background-color: #121212;
      color: #B3B3B3;
      font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
      padding: 40px;
    }}
    h1 {{
      color: #1DB954;
      margin-bottom: 10px;
    }}
    p {{
      margin: 8px 0;
    }}
    a, button {{
      display: inline-block;
      margin-top: 20px;
      padding: 12px 25px;
      color: white;
      background-color: #1DB954;
      border-radius: 40px;
      font-size: 1rem;
      text-decoration: none;
      border: none;
      cursor: pointer;
      transition: background-color 0.3s ease;
    }}
    a:hover, button:hover {{
      background-color: #17a347;
    }}
  </style>
</head>
<body>
  <h1>Welcome, {display_name}!</h1>
  <p><strong>User ID:</strong> {user_id}</p>
  <p><strong>Email:</strong> {email}</p>
  <a href="{url_for('copy_songs')}">Copy Liked Songs to Playlist</a><br />
  <a href="{url_for('logout')}">Logout</a>
</body>
</html>'''

@app.route('/copy_songs')
def copy_songs():
    token_info = session.get('token_info')
    if not token_info:
        return redirect(url_for('login'))

    sp = spotipy.Spotify(auth=token_info['access_token'])
    user_id = sp.me()["id"]

    # Create a new playlist
    playlist = sp.user_playlist_create(user=user_id, name="Your Songs", public=False)
    playlist_id = playlist["id"]

    # Fetch first 100 liked songs using limit and offset
    songs = []
    for offset in [0, 50]:
        results = sp.current_user_saved_tracks(limit=50, offset=offset)
        songs.extend(results["items"])
        if results["next"] is None:
            break  # No more tracks

    # Add songs in chunks of 100 (Spotify API limit)
    track_uris = [item["track"]["uri"] for item in songs]
    for i in range(0, len(track_uris), 100):
        sp.playlist_add_items(playlist_id, track_uris[i:i + 100])

    return "✅ Playlist created successfully!"


@app.route('/logout')
def logout():
    session.clear()
    if os.path.exists(".cache"):
        os.remove(".cache")
    return redirect(url_for("login"))

if __name__ == '__main__':
    app.run(port=8888, debug=True)
