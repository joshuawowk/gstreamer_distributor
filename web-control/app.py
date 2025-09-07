#!/usr/bin/env python3
from flask import Flask, render_template, request, jsonify
import os
import subprocess
import json

app = Flask(__name__)

@app.route('/')
def index():
    # Scan media directory and return available files
    media_files = []
    media_dir = '/media-library'
    
    if os.path.exists(media_dir):
        for root, dirs, files in os.walk(media_dir):
            for file in files:
                if file.endswith(('.mp4', '.mkv', '.avi', '.mov')):
                    relative_path = os.path.relpath(os.path.join(root, file), media_dir)
                    media_files.append(relative_path)
    
    return render_template('index.html', media_files=media_files)

@app.route('/api/stream/start', methods=['POST'])
def start_stream():
    data = request.json
    media_file = data.get('file')
    displays = data.get('displays', [])
    
    # TODO: Implement GStreamer pipeline creation
    return jsonify({'status': 'started', 'file': media_file})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
