from flask import Flask, render_template, request, jsonify, Response
import os
import socket
import threading
import webbrowser
import platform
import subprocess
import json
import time
from .core import get_precipitation

app = Flask(__name__)
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0

# Global dictionary to store progress by request_id (simple for local use)
progress_data = {}


@app.after_request
def add_no_cache_headers(response):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/open', methods=['POST'])
def open_file():
    data = request.get_json(silent=True) or {}
    filepath = data.get('file')
    if filepath and os.path.exists(filepath):
        try:
            if platform.system() == 'Windows':
                os.startfile(filepath)
            elif platform.system() == 'Darwin': # macOS
                subprocess.call(('open', filepath))
            else: # linux
                subprocess.call(('xdg-open', filepath))
            return jsonify({"status": "success"})
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 500
    return jsonify({"status": "error", "message": "File not found"}), 404

@app.route('/api/progress/<request_id>')
def get_progress_stream(request_id):
    def generate():
        while True:
            # Check if progress exists for this ID
            percent = progress_data.get(request_id, 0)
            yield f"data: {percent}\n\n"
            if percent >= 100:
                # Give client time to receive last update
                time.sleep(1)
                break
            time.sleep(0.5)
    return Response(generate(), mimetype='text/event-stream')

@app.route('/api/download', methods=['POST'])
def download():
    data = request.get_json(silent=True) or {}
    request_id = data.get('request_id', 'default')
    progress_data[request_id] = 0
    
    def update_progress(p):
        progress_data[request_id] = p

    try:
        selection_mode = data.get("selection_mode", "point")
        required = ["lat", "lon", "start_datetime", "end_datetime", "username", "password", "run_type", "freq", "interp_method"]
        if selection_mode in {"country", "square"}:
            required.append("bbox")
        missing = [field for field in required if field not in data]
        if missing:
            raise ValueError(f"Missing required fields: {', '.join(missing)}")

        out_dir = os.getcwd()
        excel_path, records = get_precipitation(
            lat=data['lat'],
            lon=data['lon'],
            start_datetime=data['start_datetime'],
            end_datetime=data['end_datetime'],
            username=data['username'],
            password=data['password'],
            run_type=data['run_type'],
            freq=data['freq'],
            interp_method=data['interp_method'],
            out_dir=out_dir,
            progress_callback=update_progress,
            selection_mode=selection_mode,
            bbox=data.get("bbox"),
            geometry=data.get("geometry"),
            region_name=data.get("region_name"),
        )
        # Ensure 100% is set
        progress_data[request_id] = 100
        return jsonify({"status": "success", "file": excel_path, "data": records})
    except Exception as e:
        progress_data[request_id] = 100 # Stop stream on error
        return jsonify({"status": "error", "message": str(e)}), 400


def _find_free_port(preferred_port=5000):
    for port in range(preferred_port, preferred_port + 50):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            try:
                sock.bind(("127.0.0.1", port))
            except OSError:
                continue
            return port
    raise RuntimeError("Could not find a free local port for imergpy.")


def start_server():
    port = int(os.environ.get("IMERGPY_PORT", _find_free_port(5000)))
    url = f"http://127.0.0.1:{port}/"

    if not os.environ.get("WERKZEUG_RUN_MAIN"):
        threading.Timer(1.25, lambda: webbrowser.open(url)).start()
    
    print("\nStarting imergpy interface...")
    print(f"Serving package from: {os.path.dirname(__file__)}")
    print(f"If your browser does not open automatically, go to: {url}\n")
    app.run(host="127.0.0.1", port=port, debug=False)
