import spotipy
from dotenv import load_dotenv
import datetime
import openai
import logging
import json
import os
import argparse

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def main():
    parser = argparse.ArgumentParser(description="simple cli song utility")
    parser.add_argument(
        "-p", type=str, help="The prompt to describe playlist wanted")
    parser.add_argument("-n", type=int, default=8,
                        help="The number of songs wanted")
    parser.add_argument("-envfile", type=str, default=".env",
                        required=False, help="A dotenv file with your env var")

    args = parser.parse_args()
    load_dotenv(args.envfile)
    if any([x not in os.environ for x in ("OPEN_AI_API_KEY", "CLIENT_ID", "CLIENT_SECRET")]):
        raise ValueError(
            "Error: msising environment variables. Please check your env file.")
    if args.n not in range(1, 50):
        raise ValueError("Error: n should be between 0 and 50")

    openai.api_key = os.environ["OPEN_AI_API_KEY"]

    playlist_prompt = args.p
    count = args.n
    playlist = get_playlist(playlist_prompt, count)
    add_songs_to_spotify(playlist_prompt, playlist)


def get_playlist(prompt, count=8):
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
        max_tokens=400
    )

    playlist = json.loads(response["choices"][0]["message"]["content"])
    return playlist


def add_songs_to_spotify(playlist_prompt, playlist):

    # Use your Spotify API's keypair's Client ID
    spotipy_client_id = os.environ["CLIENT_ID"]
    # Use your Spotify API's keypair's Client Secret
    spotipy_client_secret = os.environ["CLIENT_SECRET"]

    spotipy_redirect_url = "http://localhost:9999"

    spot = spotipy.Spotify(
        auth_manager=spotipy.SpotifyOAuth(
            client_id=spotipy_client_id,
            client_secret=spotipy_client_secret,
            redirect_uri=spotipy_redirect_url,
            scope="playlist-modify-private"
        )
    )

    current_user = spot.current_user()

    assert current_user is not None

    track_ids = []

    for item in playlist:
        artist, song = item["artist"], item["song"]

        advanced_query = f"artist:({artist}) track:({song})"
        basic_query = f"{song} {artist}"

        for query in [advanced_query, basic_query]:
            log.debug(f"Searching for query: {query}")
            search_results = spot.search(
                q=query, limit=10, type="track")  # , market=market)

            if not search_results["tracks"]["items"] or search_results["tracks"]["items"][0]["popularity"] < 20:
                continue
            else:
                good_guess = search_results["tracks"]["items"][0]
                print(f"Found: {good_guess['name']} [{good_guess['id']}]")
                # print(f"FOUND USING QUERY: {query}")
                track_ids.append(good_guess["id"])
                break

        else:
            print(
                f"Queries {advanced_query} and {basic_query} returned no good results. Skipping.")

    created_playlist = spot.user_playlist_create(
        current_user["id"],
        public=False,
        name=f"{playlist_prompt} ({datetime.datetime.now().strftime('%c')})",
    )


    spot.user_playlist_add_tracks(
        current_user["id"], created_playlist["id"], track_ids)

if __name__ == "__main__":
    main()
