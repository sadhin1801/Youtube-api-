from flask import Flask, request, jsonify
import yt_dlp
import os

app = Flask(__name__)


@app.get("/")
def home():
    return jsonify({
        "status": True,
        "message": "Song API is running",
        "endpoints": [
            "/ytFullSearch?songName=",
            "/ytDl3?link="
        ]
    })


@app.get("/ytFullSearch")
def search():

    keyword = request.args.get("songName", "").strip()

    if not keyword:
        return jsonify({
            "status": False,
            "error": "songName is required"
        }), 400

    try:

        options = {
            "quiet": True,
            "no_warnings": True,
            "extract_flat": True,
            "noplaylist": True
        }

        with yt_dlp.YoutubeDL(options) as ydl:

            data = ydl.extract_info(
                f"ytsearch6:{keyword}",
                download=False
            )

        results = []

        for item in data.get("entries", []):

            if not item:
                continue

            results.append({
                "id": item.get("id"),
                "title": item.get("title"),
                "url": item.get("url"),
                "thumbnail":
                    item.get("thumbnail"),
                "duration":
                    item.get("duration")
            })

        return jsonify(results)

    except Exception as e:

        return jsonify({
            "status": False,
            "error": str(e)
        }), 500


@app.get("/ytDl3")
def audio_info():

    url = request.args.get("link", "").strip()

    if not url:
        return jsonify({
            "status": False,
            "error": "link is required"
        }), 400

    try:

        options = {
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True
        }

        with yt_dlp.YoutubeDL(options) as ydl:

            info = ydl.extract_info(
                url,
                download=False
            )

        return jsonify({
            "status": True,
            "id": info.get("id"),
            "title": info.get("title"),
            "duration": info.get("duration"),
            "thumbnail": info.get("thumbnail"),
            "webpage_url": info.get("webpage_url")
        })

    except Exception as e:

        return jsonify({
            "status": False,
            "error": str(e)
        }), 500


if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=int(
            os.environ.get("PORT", 5000)
        )
          )
