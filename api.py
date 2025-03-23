from flask import Flask, jsonify, request
from flask_cors import CORS
from control import OP25Controller
from ch_manager import ChannelManager  # This module now uses the revised helper functions
import os
from datetime import datetime
import re
import subprocess, os, signal
from logMonitor import logMonitorOP25, LogFileWatcher
import logging

# Initialize Flask app
app = Flask(__name__)
CORS(app, supports_credentials=True, resources={r"/*": {"origins": "*"}})

# Configure logging
logging.basicConfig(level=logging.DEBUG)


# NEW API ENDPOINTS

# /channel/<int:channel_number>/zone
@app.route('/channel/<int:channel_number>/zone', methods=['GET'])
def channel_zone(channel_number):
    data = file_obj.getZoneByChannelNumber(channel_number)
    return jsonify(data), 200

# GET CHANNEL BY NUMBER & ZONE
@app.route('/zone/<int:zone_number>/channel/<int:channel_number>/', methods=['GET'])
def channel(zone_number, channel_number):
    data = file_obj.getChannel(zone_number, channel_number)
    return jsonify(data), 200

# NEXT CHANNEL
@app.route('/zone/<int:zone_number>/channel/<int:channel_number>/next', methods=['GET'])
def channel_next(zone_number, channel_number):
    _channel = file_obj.nextChannel(zone_number, channel_number)
    return jsonify(_channel), 200

# PREVIOUS CHANNEL
@app.route('/zone/<int:zone_number>/channel/<int:channel_number>/previous', methods=['GET'])
def channel_previous(zone_number, channel_number):
    _channel = file_obj.previousChannel(zone_number, channel_number)
    return jsonify(_channel), 200

## * GET ALL ZONES *
@app.route('/zones', methods=['GET'])
def zones():
    # logging.debug("Fetching all zones")
    data = file_obj.getAllZones()
    if not data or "zones" not in data:
        return jsonify({"error": "No zones found"}), 404
    return jsonify(data), 200

## * GET ZONE *
@app.route('/zone/<int:zone_number>', methods=['GET'])
def get_zone(zone_number):
    _zone = file_obj.getZoneByIndex(zone_number)
    return jsonify(_zone), 200

## * PREVIOUS ZONE *
@app.route('/zone/<int:zone_number>/previous', methods=['GET'])
def zone_previous(zone_number):
    data = file_obj.previousZone(zone_number) #!
    return jsonify(data), 200

## * GET NEXT ZONE *
@app.route('/zone/<int:zone_number>/next', methods=['GET'])
def zone_next(zone_number):
    _zone = file_obj.nextZone(zone_number)
    return jsonify(_zone), 200


@app.route('/whitelist', methods=['POST'])
def whitelist():
    payload = request.get_json() or {}
    tgids = payload.get("tgid", [])

    if not tgids:
        return jsonify({
            "error": "No TGIDs provided",
            "payload": payload  # Include full request data for debugging
        }), 400

    op25.switchGroup(tgids)
    return jsonify({
        "message": "TGIDs added to whitelist",
        "payload": payload
    }), 200

### RESTART OP25
@app.route('/restart', methods=['POST'])
def restart():
    # logging.debug("Restarting OP25")
    op25.restart()
    return jsonify({"message": "OP25 restarted"}), 200

if __name__ == '__main__':
    http_proc = None
    try:
        # Initialize controllers and managers
        op25 = OP25Controller()
        op25.start()
        file_obj = ChannelManager('/opt/op25-project/systems-2.json')
        
        # Launch the front-end static server
        http_proc = subprocess.Popen([
            "python3", "-m", "http.server", "8000",
            "--directory", "/opt/op25-project/html"
        ])
        
        # Start the Flask API
        app.run(host='0.0.0.0', port=5001, debug=True, use_reloader=False)
    
    except Exception as e:
        logging.error(f"Fatal error during startup: {e}")
    
    finally:
        if http_proc is not None:
            http_proc.terminate()
            http_proc.wait()