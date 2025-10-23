# dashboard_server.py
# ---------------------
# Flask backend for Signal Trader Web Dashboard
# Provides REST API and WebSocket support for real-time monitoring

from flask import Flask, render_template, jsonify, request, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import yaml
import json
import threading
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Flask app setup
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Paths
CHANNELS_CONFIG = Path("channels.yaml")
HISTORY_DIR = Path("history")
ORDERS_DIR = Path("orders_out")
STATUS_DIR = Path("status_out")
STATUS_LOG = Path("status_log.jsonl")

# In-memory cache
channel_stats = {}
recent_signals = []
system_stats = {
    'uptime_start': datetime.now(),
    'total_messages': 0,
    'total_signals': 0,
    'total_trades': 0
}

# ==================== CONFIG MANAGEMENT ====================

def load_channels_config() -> Dict[str, Any]:
    """Load channels configuration from YAML"""
    try:
        if not CHANNELS_CONFIG.exists():
            return {'channels': [], 'global': {}}
        
        with open(CHANNELS_CONFIG, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        return {'channels': [], 'global': {}}

def save_channels_config(config: Dict[str, Any]) -> bool:
    """Save channels configuration to YAML"""
    try:
        with open(CHANNELS_CONFIG, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)
        return True
    except Exception as e:
        logger.error(f"Failed to save config: {e}")
        return False

# ==================== STATISTICS ====================

def get_channel_history_file(channel_username: str) -> Path:
    """Get history file path for a channel"""
    safe_name = channel_username.replace('@', '').replace('/', '_')
    return HISTORY_DIR / f"{safe_name}_history.txt"

def calculate_channel_stats():
    """Calculate statistics for all channels"""
    global channel_stats, recent_signals
    
    config = load_channels_config()
    stats = {}
    all_signals = []
    
    for channel in config.get('channels', []):
        username = channel['username']
        history_file = get_channel_history_file(username)
        
        # Initialize stats
        channel_stat = {
            'name': channel['name'],
            'username': username,
            'enabled': channel.get('enabled', False),
            'messages_total': 0,
            'messages_today': 0,
            'messages_this_week': 0,
            'last_message': None,
            'last_message_text': None,
            'instruments': channel.get('instruments', []),
            'parser_type': channel.get('parser_type', 'standard'),
            'risk_per_trade': channel.get('risk_per_trade', 1.0)
        }
        
        # Read history file if exists
        if history_file.exists():
            try:
                with open(history_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                channel_stat['messages_total'] = len(lines)
                
                now = datetime.now()
                today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
                week_start = now - timedelta(days=7)
                
                for line in lines:
                    try:
                        timestamp_str, message = line.split('\t', 1)
                        msg_time = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                        
                        # Count messages
                        if msg_time >= today_start:
                            channel_stat['messages_today'] += 1
                        if msg_time >= week_start:
                            channel_stat['messages_this_week'] += 1
                        
                        # Store recent signals
                        all_signals.append({
                            'timestamp': msg_time.isoformat(),
                            'channel': channel['name'],
                            'message': message.strip(),
                            'username': username
                        })
                        
                    except Exception:
                        continue
                
                # Get last message
                if lines:
                    try:
                        last_line = lines[-1]
                        timestamp_str, message = last_line.split('\t', 1)
                        msg_time = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                        
                        time_ago = now - msg_time.replace(tzinfo=None)
                        if time_ago.total_seconds() < 60:
                            channel_stat['last_message'] = f"{int(time_ago.total_seconds())} sec ago"
                        elif time_ago.total_seconds() < 3600:
                            channel_stat['last_message'] = f"{int(time_ago.total_seconds() / 60)} min ago"
                        elif time_ago.total_seconds() < 86400:
                            channel_stat['last_message'] = f"{int(time_ago.total_seconds() / 3600)} hr ago"
                        else:
                            channel_stat['last_message'] = f"{int(time_ago.total_seconds() / 86400)} days ago"
                        
                        channel_stat['last_message_text'] = message.strip()[:100]
                    except Exception:
                        pass
                        
            except Exception as e:
                logger.error(f"Error reading history for {username}: {e}")
        
        stats[username] = channel_stat
    
    # Sort signals by time (most recent first)
    all_signals.sort(key=lambda x: x['timestamp'], reverse=True)
    recent_signals = all_signals[:50]  # Keep last 50 signals
    
    channel_stats = stats
    
    # Update system stats
    system_stats['total_messages'] = sum(s['messages_total'] for s in stats.values())

def update_stats_periodically():
    """Background thread to update statistics"""
    while True:
        try:
            calculate_channel_stats()
            
            # Emit update to all connected clients
            socketio.emit('stats_update', {
                'channel_stats': channel_stats,
                'recent_signals': recent_signals[:10],
                'system_stats': {
                    'uptime': str(datetime.now() - system_stats['uptime_start']).split('.')[0],
                    'total_messages': system_stats['total_messages'],
                    'total_signals': system_stats['total_signals'],
                    'total_trades': system_stats['total_trades']
                }
            })
        except Exception as e:
            logger.error(f"Error in stats update: {e}")
        
        time.sleep(5)  # Update every 5 seconds

# ==================== API ROUTES ====================

@app.route('/')
def index():
    """Serve main dashboard"""
    return send_from_directory('.', 'dashboard.html')

@app.route('/api/config', methods=['GET'])
def get_config():
    """Get current configuration"""
    try:
        config = load_channels_config()
        return jsonify({
            'success': True,
            'config': config
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/config', methods=['POST'])
def update_config():
    """Update configuration"""
    try:
        new_config = request.json
        if save_channels_config(new_config):
            calculate_channel_stats()  # Recalculate immediately
            return jsonify({
                'success': True,
                'message': 'Configuration updated successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to save configuration'
            }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/channels', methods=['GET'])
def get_channels():
    """Get all channels with stats"""
    try:
        config = load_channels_config()
        channels_with_stats = []
        
        for channel in config.get('channels', []):
            username = channel['username']
            stats = channel_stats.get(username, {})
            
            channels_with_stats.append({
                **channel,
                'stats': stats
            })
        
        return jsonify({
            'success': True,
            'channels': channels_with_stats
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/channels/<channel_username>', methods=['GET'])
def get_channel(channel_username):
    """Get specific channel details"""
    try:
        config = load_channels_config()
        
        for channel in config.get('channels', []):
            if channel['username'] == f"@{channel_username}" or channel['username'] == channel_username:
                stats = channel_stats.get(channel['username'], {})
                return jsonify({
                    'success': True,
                    'channel': {
                        **channel,
                        'stats': stats
                    }
                })
        
        return jsonify({
            'success': False,
            'error': 'Channel not found'
        }), 404
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/channels', methods=['POST'])
def add_channel():
    """Add a new channel"""
    try:
        new_channel = request.json
        
        # Validate required fields
        required = ['name', 'username']
        if not all(field in new_channel for field in required):
            return jsonify({
                'success': False,
                'error': 'Missing required fields'
            }), 400
        
        # Add @ if not present
        if not new_channel['username'].startswith('@'):
            new_channel['username'] = f"@{new_channel['username']}"
        
        # Set defaults
        new_channel.setdefault('enabled', True)
        new_channel.setdefault('auto_parse', True)
        new_channel.setdefault('auto_trade', False)
        new_channel.setdefault('parser_type', 'standard')
        new_channel.setdefault('risk_per_trade', 1.0)
        new_channel.setdefault('instruments', ['XAUUSD'])
        new_channel.setdefault('notes', '')
        
        # Load config and add channel
        config = load_channels_config()
        config.setdefault('channels', [])
        
        # Check if channel already exists
        if any(ch['username'] == new_channel['username'] for ch in config['channels']):
            return jsonify({
                'success': False,
                'error': 'Channel already exists'
            }), 400
        
        config['channels'].append(new_channel)
        
        if save_channels_config(config):
            calculate_channel_stats()
            return jsonify({
                'success': True,
                'message': 'Channel added successfully',
                'channel': new_channel
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to save configuration'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/channels/<channel_username>', methods=['PUT'])
def update_channel(channel_username):
    """Update a channel"""
    try:
        updates = request.json
        config = load_channels_config()
        
        # Find and update channel
        found = False
        for i, channel in enumerate(config.get('channels', [])):
            if channel['username'] == f"@{channel_username}" or channel['username'] == channel_username:
                config['channels'][i].update(updates)
                found = True
                break
        
        if not found:
            return jsonify({
                'success': False,
                'error': 'Channel not found'
            }), 404
        
        if save_channels_config(config):
            calculate_channel_stats()
            return jsonify({
                'success': True,
                'message': 'Channel updated successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to save configuration'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/channels/<channel_username>', methods=['DELETE'])
def delete_channel(channel_username):
    """Delete a channel"""
    try:
        config = load_channels_config()
        
        # Filter out the channel
        original_count = len(config.get('channels', []))
        config['channels'] = [
            ch for ch in config.get('channels', [])
            if ch['username'] not in [f"@{channel_username}", channel_username]
        ]
        
        if len(config['channels']) == original_count:
            return jsonify({
                'success': False,
                'error': 'Channel not found'
            }), 404
        
        if save_channels_config(config):
            calculate_channel_stats()
            return jsonify({
                'success': True,
                'message': 'Channel deleted successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to save configuration'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/signals/recent', methods=['GET'])
def get_recent_signals():
    """Get recent signals across all channels"""
    try:
        limit = int(request.args.get('limit', 50))
        return jsonify({
            'success': True,
            'signals': recent_signals[:limit]
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get system statistics"""
    try:
        config = load_channels_config()
        enabled_count = sum(1 for ch in config.get('channels', []) if ch.get('enabled', False))
        
        return jsonify({
            'success': True,
            'stats': {
                'total_channels': len(config.get('channels', [])),
                'enabled_channels': enabled_count,
                'uptime': str(datetime.now() - system_stats['uptime_start']).split('.')[0],
                'total_messages': system_stats['total_messages'],
                'total_signals': system_stats['total_signals'],
                'total_trades': system_stats['total_trades']
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ==================== WEBSOCKET ====================

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    logger.info(f"Client connected")
    emit('connected', {'message': 'Connected to Signal Trader Dashboard'})
    
    # Send initial data
    emit('stats_update', {
        'channel_stats': channel_stats,
        'recent_signals': recent_signals[:10],
        'system_stats': {
            'uptime': str(datetime.now() - system_stats['uptime_start']).split('.')[0],
            'total_messages': system_stats['total_messages'],
            'total_signals': system_stats['total_signals'],
            'total_trades': system_stats['total_trades']
        }
    })

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    logger.info(f"Client disconnected")

# ==================== MAIN ====================

if __name__ == '__main__':
    # Initial stats calculation
    calculate_channel_stats()
    
    # Start background stats updater
    stats_thread = threading.Thread(target=update_stats_periodically, daemon=True)
    stats_thread.start()
    
    logger.info("Starting Signal Trader Dashboard Server")
    logger.info("Dashboard will be available at: http://localhost:5000")
    
    # Run server
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)
