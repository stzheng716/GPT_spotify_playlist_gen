import spotipy
from dotenv import dotenv_values
import openai
import json

config = dotenv_values(".env")

openai.api_key = config["OPEN_AI_API_KEY"]

def get_playlist(prompt, count = 8):
    example_json = """
    [
        {"song": "Someone Like You", "artist": "Adele"},
        {"song": "Hurt", "artist": "Johnny Cash"},
        {"song": "Nothing Compares 2 U", "artist": "Sinéad O'Connor"},
        {"song": "Fix You", "artist": "Coldplay"},
        {"song": "Tears in Heaven", "artist": "Eric Clapton"},
        {"song": "Skinny Love", "artist": "Bon Iver"},
        {"song": "Yesterday", "artist": "The Beatles"},
        {"song": "My Immortal", "artist": "Evanescence"},
        {"song": "All By Myself", "artist": "Céline Dion"},
        {"song": "Hallelujah", "artist": "Jeff Buckley"}
      ]
    """

    messages = [
        {"role": "system", "content": """You are a helpful playlist generating assistant. You should generate a 
        list of songs and their artists according to a text prompt. You should return a JSON array, where each 
        element fallows this format: {"song": <song_title>, "artist": <artist_name>}"""},
        {"role": "user", "content": "Generate a playlist of songs based on this prompt: super super sad songs"},
        {"role": "assistant", "content": example_json},
        {"role": "user", "content": f"Generate a playlist of {count} songs based on this prompt: {prompt}"},
    ]

    response = openai.ChatCompletion.create(
        messages=messages,
        model="gpt-3.5-turbo",
        max_tokens = 400
    )

    playlist = json.loads(response["choices"][0]["message"]["content"])
    return playlist

playlist = get_playlist("epic songs", 4)


spot = spotipy.Spotify(
    auth_manager=spotipy.SpotifyOAuth(
        client_id=config["CLIENT_ID"],
        client_secret=config["CLIENT_SECRET"],
        redirect_uri="http://localhost:9999",
        scope="playlist-modify-private"
    )
)

current_user = spot.current_user()

track_ids = []

assert current_user is not None

for item in playlist:
    artist, song = item["artist"], item["song"]
    query = f"{song} {artist}"

    search_results = spot.search(q=query, type="track", limit=3)

    track_ids.append(search_results["tracks"]["items"][0]["id"])

created_playlist = spot.user_playlist_create(
    current_user["id"],
    public=False,
    name="TEST_GPT_PLAYLIST1"
)

spot.user_playlist_add_tracks(current_user["id"], created_playlist["id"], track_ids)