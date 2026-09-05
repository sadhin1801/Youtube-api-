import os
import uuid
import time
import threading
from flask import Flask, request, jsonify, send_file
import yt_dlp

app = Flask(__name__)

DOWNLOAD_DIR = "downloads"
FILE_LIFETIME = 30 * 60

os.makedirs(DOWNLOAD_DIR, exist_ok=True)


def cleanup_worker():
    while True:
        try:
            now = time.time()

            for filename in os.listdir(DOWNLOAD_DIR):
                path = os.path.join(DOWNLOAD_DIR, filename)

                try:
                    if now - os.path.getmtime(path) > FILE_LIFETIME:
                        os.remove(path)
                except Exception:
                    pass

        except Exception:
            pass

        time.sleep(300)


threading.Thread(
    target=cleanup_worker,
    daemon=True
).start()


@app.route("/")
def index():
    return jsonify({
        "status": True,
        "name": "Messenger Song Audio API",
        "version": "1.0",
        "endpoints": [
            "/ytFullSearch?songName=",
            "/ytDl3?link=",
            "/download/<filename>"
        ]
    })


@app.route("/ytFullSearch")
def yt_search():

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
            "skip_download": True,
            "noplaylist": True
        }

        with yt_dlp.YoutubeDL(options) as ydl:

            result = ydl.extract_info(
                f"ytsearch6:{keyword}",
                download=False
            )

        results = []

        for item in result.get("entries", []):

            if not item:
                continue

            video_id = item.get("id")

            if not video_id:
                continue

            results.append({
                "id": video_id,
                "title": item.get("title"),
                "url": (
                    f"https://www.youtube.com/watch?v={video_id}"
                ),
                "thumbnail": (
                    f"https://i.ytimg.com/vi/"
                    f"{video_id}/hqdefault.jpg"
                ),
                "duration": item.get("duration")
            })

        return jsonify(results)

    except Exception as e:

        return jsonify({
            "status": False,
            "error": str(e)
        }), 500


@app.route("/ytDl3")
def yt_audio():

    url = request.args.get("link", "").strip()

    if not url:
        return jsonify({
            "status": False,
            "error": "link is required"
        }), 400

    file_id = uuid.uuid4().hex
    output = os.path.join(
        DOWNLOAD_DIR,
        file_id + ".%(ext)s"
    )

    options = {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,

        "format": "bestaudio/best",

        "outtmpl": output,

        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "128"
            }
        ],

        "socket_timeout": 30,
        "retries": 3,
        "fragment_retries": 3
    }

    try:

        with yt_dlp.YoutubeDL(options) as ydl:

            info = ydl.extract_info(
                url,
                download=True
            )

        title = info.get("title", "audio")

        filename = file_id + ".mp3"
        filepath = os.path.join(
            DOWNLOAD_DIR,
            filename
        )

        if not os.path.exists(filepath):

            return jsonify({
                "status": False,
                "error": "Audio file was not created"
            }), 500

        base_url = request.host_url.rstrip("/")

        download_link = (
            f"{base_url}/download/{filename}"
        )

        return jsonify({
            "status": True,
            "title": title,
            "downloadLink": download_link,
            "filename": filename,
            "format": "mp3"
        })

    except Exception as e:

        # Remove incomplete files
        try:
            for filename in os.listdir(DOWNLOAD_DIR):

                if filename.startswith(file_id):

                    os.remove(
                        os.path.join(
                            DOWNLOAD_DIR,
                            filename
                        )
                    )

        except Exception:
            pass

        return jsonify({
            "status": False,
            "error": str(e)
        }), 500


@app.route("/download/<filename>")
def download_audio(filename):

    # Prevent path traversal
    if "/" in filename or "\\" in filename:
        return jsonify({
            "status": False,
            "error": "Invalid filename"
        }), 400

    filepath = os.path.join(
        DOWNLOAD_DIR,
        filename
    )

    if not os.path.isfile(filepath):

        return jsonify({
            "status": False,
            "error": "Audio expired or not found"
        }), 404

    return send_file(
        filepath,
        mimetype="audio/mpeg",
        as_attachment=False,
        download_name=filename
    )


if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000))
    )
