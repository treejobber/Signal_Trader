# telegram_harvester_multi.py
# --------------------------------
# Multi-channel Telegram signal harvester
# Monitors multiple channels simultaneously with individual settings per channel

import os, json, uuid, threading, time, logging, yaml
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

from telethon import TelegramClient, events

# --- optional .env support ---
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

# ===================== LOGGING SETUP =====================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s - %(message)s',
    handlers=[
        logging.FileHandler('telegram_harvester_multi.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)
# =========================================================

# ===================== CONFIGURATION =====================
@dataclass
class ChannelConfig:
    """Configuration for a single channel"""
    name: str
    username: str
    enabled: bool
    auto_parse: bool
    auto_trade: bool
    parser_type: str
    risk_per_trade: float
    instruments: List[str]
    notes: str = ""

class Config:
    """Global configuration manager"""
    def __init__(self, config_file: str = "channels.yaml"):
        self.config_file = Path(config_file)
        self.channels: List[ChannelConfig] = []
        self.global_config: Dict[str, Any] = {}
        self.load()
    
    def load(self):
        """Load configuration from YAML file"""
        try:
            if not self.config_file.exists():
                logger.error(f"Config file not found: {self.config_file}")
                raise FileNotFoundError(f"Config file not found: {self.config_file}")
            
            with open(self.config_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            # Load channels
            self.channels = []
            for ch in data.get('channels', []):
                channel = ChannelConfig(
                    name=ch['name'],
                    username=ch['username'],
                    enabled=ch.get('enabled', True),
                    auto_parse=ch.get('auto_parse', True),
                    auto_trade=ch.get('auto_trade', False),
                    parser_type=ch.get('parser_type', 'standard'),
                    risk_per_trade=ch.get('risk_per_trade', 1.0),
                    instruments=ch.get('instruments', []),
                    notes=ch.get('notes', '')
                )
                self.channels.append(channel)
            
            # Load global config
            self.global_config = data.get('global', {})
            
            logger.info(f"Loaded {len(self.channels)} channels from config")
            enabled_count = sum(1 for ch in self.channels if ch.enabled)
            logger.info(f"{enabled_count} channels enabled for monitoring")
            
        except Exception as e:
            logger.error(f"Failed to load config: {e}", exc_info=True)
            raise
    
    def get_enabled_channels(self) -> List[ChannelConfig]:
        """Get list of enabled channels"""
        return [ch for ch in self.channels if ch.enabled]
    
    def get_channel_by_username(self, username: str) -> Optional[ChannelConfig]:
        """Get channel config by username"""
        for ch in self.channels:
            if ch.username == username:
                return ch
        return None

# Load configuration
config = Config()

# Telegram API credentials
API_ID = int(os.getenv("API_ID", "0"))
if API_ID == 0:
    logger.error("API_ID not set in environment variables")
    raise ValueError("API_ID must be set in environment")

API_HASH = os.getenv("API_HASH", "")
if not API_HASH:
    logger.error("API_HASH not set in environment variables")
    raise ValueError("API_HASH must be set in environment")

SESSION_NAME = config.global_config.get('session', {}).get('name', 'TelegramReader')
BACKFILL_LIMIT = int(os.getenv("BACKFILL_LIMIT", "100"))

# Files / folders
ORDERS_DIR = Path("orders_out")
STATUS_DIR = Path("status_out")
PROCESSED_DIR = STATUS_DIR / "processed"
STATUS_LOG = Path("status_log.jsonl")
HISTORY_DIR = Path("history")  # Per-channel history files

# Create directories
for p in (ORDERS_DIR, STATUS_DIR, PROCESSED_DIR, HISTORY_DIR):
    try:
        p.mkdir(exist_ok=True, parents=True)
        logger.info(f"Ensured directory exists: {p}")
    except Exception as e:
        logger.error(f"Failed to create directory {p}: {e}", exc_info=True)
        raise
# ==================================================

client = TelegramClient(SESSION_NAME, API_ID, API_HASH)

# Channel statistics tracking
channel_stats = {}

def get_channel_history_file(channel_username: str) -> Path:
    """Get history file path for a specific channel"""
    # Remove @ symbol and make filename safe
    safe_name = channel_username.replace('@', '').replace('/', '_')
    return HISTORY_DIR / f"{safe_name}_history.txt"

# ------------- STEP C: command emitter with robust error handling -------------
def emit_command(cmd: Dict[str, Any], channel_name: str = None) -> Optional[Path]:
    """
    Write a command JSON for NinjaTrader to pick up using atomic file operations.
    Now includes channel name for tracking.
    """
    try:
        # Ensure command has an ID
        if "id" not in cmd:
            cmd["id"] = str(uuid.uuid4())
        
        # Add channel name if provided
        if channel_name:
            cmd["channel"] = channel_name
        
        # Validate required fields
        if "cmd" not in cmd:
            logger.error(f"Command missing 'cmd' field: {cmd}")
            return None
        
        # Define final path
        final_path = ORDERS_DIR / f"CMD_{cmd['id']}.json"
        
        # Write to temporary file first (atomic operation)
        temp_path = final_path.with_suffix('.tmp')
        
        try:
            json_content = json.dumps(cmd, ensure_ascii=False, indent=2)
        except (TypeError, ValueError) as e:
            logger.error(f"Failed to serialize command to JSON: {e}", exc_info=True)
            return None
        
        try:
            temp_path.write_text(json_content, encoding="utf-8")
            logger.debug(f"Wrote temporary file: {temp_path}")
        except IOError as e:
            logger.error(f"Failed to write temporary file {temp_path}: {e}", exc_info=True)
            return None
        
        try:
            temp_path.rename(final_path)
            logger.info(f"[CMD] Wrote {final_path.name} ({cmd.get('cmd')}) for signal {cmd.get('signal')} from {channel_name}")
            return final_path
        except OSError as e:
            logger.error(f"Failed to rename {temp_path} to {final_path}: {e}", exc_info=True)
            try:
                if temp_path.exists():
                    temp_path.unlink()
            except Exception as cleanup_error:
                logger.error(f"Failed to cleanup temp file {temp_path}: {cleanup_error}")
            return None
            
    except Exception as e:
        logger.error(f"Unexpected error in emit_command: {e}", exc_info=True)
        return None

# ------------- STEP D: status watcher -------------
def handle_status(evt: Dict[str, Any]) -> bool:
    """Handle status event from NinjaTrader"""
    try:
        if not isinstance(evt, dict):
            logger.error(f"Status event is not a dictionary: {type(evt)}")
            return False
        
        evt_type = evt.get('evt', 'UNKNOWN')
        signal_id = evt.get('signal', 'UNKNOWN')
        
        try:
            json_line = json.dumps(evt, ensure_ascii=False)
        except (TypeError, ValueError) as e:
            logger.error(f"Failed to serialize status event: {e}", exc_info=True)
            return False
        
        try:
            with STATUS_LOG.open("a", encoding="utf-8") as f:
                f.write(json_line + "\n")
        except IOError as e:
            logger.error(f"Failed to write to status log: {e}", exc_info=True)
            return False
        
        logger.info(f"[STAT] {evt_type} for signal={signal_id}")
        return True
        
    except Exception as e:
        logger.error(f"Unexpected error in handle_status: {e}", exc_info=True)
        return False

def watch_status_folder(stop_event: threading.Event):
    """Poll status_out/ for new JSON files"""
    seen = set()
    logger.info("Status watcher thread started")
    
    while not stop_event.is_set():
        try:
            json_files = list(STATUS_DIR.glob("*.json"))
            
            for p in json_files:
                if p.name in seen:
                    continue
                
                try:
                    try:
                        content = p.read_text(encoding="utf-8")
                    except IOError as e:
                        logger.error(f"Failed to read status file {p.name}: {e}")
                        continue
                    
                    try:
                        data = json.loads(content)
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse JSON in {p.name}: {e}")
                        seen.add(p.name)
                        try:
                            corrupted_path = PROCESSED_DIR / f"CORRUPT_{p.name}"
                            p.rename(corrupted_path)
                        except Exception:
                            pass
                        continue
                    
                    if handle_status(data):
                        seen.add(p.name)
                        try:
                            dest_path = PROCESSED_DIR / p.name
                            p.rename(dest_path)
                        except OSError as e:
                            logger.error(f"Failed to move {p.name}: {e}")
                    
                except Exception as e:
                    logger.error(f"Error processing status file {p.name}: {e}", exc_info=True)
                    
        except Exception as e:
            logger.error(f"Error in status watcher main loop: {e}", exc_info=True)
        
        time.sleep(0.5)
    
    logger.info("Status watcher thread stopped")

# ------------- Multi-channel Telegram logic -------------
async def fetch_channel_history(channel: ChannelConfig):
    """Fetch message history for a specific channel"""
    try:
        entity = await client.get_entity(channel.username)
        logger.info(f"[{channel.name}] Connected to channel: {channel.username}")
    except Exception as e:
        logger.error(f"[{channel.name}] Failed to get channel {channel.username}: {e}", exc_info=True)
        return
    
    msgs = []
    try:
        async for m in client.iter_messages(entity, limit=BACKFILL_LIMIT):
            if m.message:
                msgs.append(m)
    except Exception as e:
        logger.error(f"[{channel.name}] Error fetching message history: {e}", exc_info=True)
        if not msgs:
            return
        logger.warning(f"[{channel.name}] Partial history fetched: {len(msgs)} messages")
    
    # Write to channel-specific history file
    history_file = get_channel_history_file(channel.username)
    try:
        with history_file.open("w", encoding="utf-8") as out:
            for message in reversed(msgs):
                try:
                    iso_utc = message.date.astimezone(timezone.utc).isoformat()
                    text_one_line = message.message.replace("\n", " ").strip()
                    out.write(f"{iso_utc}\t{text_one_line}\n")
                except Exception as e:
                    logger.error(f"[{channel.name}] Error processing message {message.id}: {e}")
                    continue
        
        logger.info(f"[{channel.name}] Saved {len(msgs)} messages to {history_file.name}")
        
        # Initialize stats
        channel_stats[channel.username] = {
            'name': channel.name,
            'messages_today': 0,
            'last_message': None,
            'total_messages': len(msgs)
        }
        
    except IOError as e:
        logger.error(f"[{channel.name}] Failed to write history file: {e}", exc_info=True)

async def setup_channel_handlers():
    """Set up message handlers for all enabled channels"""
    enabled_channels = config.get_enabled_channels()
    
    if not enabled_channels:
        logger.warning("No channels enabled for monitoring!")
        return
    
    # Get all channel usernames for the event handler
    channel_usernames = [ch.username for ch in enabled_channels]
    
    @client.on(events.NewMessage(chats=channel_usernames))
    async def on_new_message(event):
        """Handle new message from any monitored channel"""
        try:
            # Determine which channel this message is from
            chat = await event.get_chat()
            channel_username = f"@{chat.username}" if hasattr(chat, 'username') and chat.username else None
            
            if not channel_username:
                logger.warning("Received message from unknown channel")
                return
            
            # Get channel config
            channel_config = config.get_channel_by_username(channel_username)
            if not channel_config:
                logger.warning(f"No config found for channel: {channel_username}")
                return
            
            text = event.raw_text.replace("\n", " ").strip()
            iso_utc = event.message.date.astimezone(timezone.utc).isoformat()
            
            # Write to channel-specific history file
            history_file = get_channel_history_file(channel_username)
            try:
                with history_file.open("a", encoding="utf-8") as out:
                    out.write(f"{iso_utc}\t{text}\n")
            except IOError as e:
                logger.error(f"[{channel_config.name}] Failed to append to history: {e}")
            
            # Update stats
            if channel_username in channel_stats:
                channel_stats[channel_username]['messages_today'] += 1
                channel_stats[channel_username]['last_message'] = datetime.now()
            
            logger.info(f"[{channel_config.name}] NEW: {text[:100]}")
            
            # TODO: Add signal parsing here based on channel_config.parser_type
            # if channel_config.auto_parse:
            #     parse_and_emit_signal(text, channel_config)
            
        except Exception as e:
            logger.error(f"Error processing new message: {e}", exc_info=True)
    
    logger.info(f"Set up handlers for {len(enabled_channels)} channels")

async def main():
    """Main entry point"""
    try:
        enabled_channels = config.get_enabled_channels()
        
        if not enabled_channels:
            logger.error("No channels enabled in configuration!")
            return
        
        logger.info(f"[OK] Monitoring {len(enabled_channels)} channels:")
        for ch in enabled_channels:
            logger.info(f"  - {ch.name} ({ch.username})")
        
        # Set up event handlers
        await setup_channel_handlers()
        
        # Backfill history for each channel
        if BACKFILL_LIMIT > 0:
            for channel in enabled_channels:
                await fetch_channel_history(channel)
        
        logger.info("[READY] Live monitoring all channels… (Ctrl+C to stop)")
        
    except Exception as e:
        logger.error(f"Error in main(): {e}", exc_info=True)
        raise

# ---------------------- run ------------------------
if __name__ == "__main__":
    # Check for pyyaml
    try:
        import yaml
    except ImportError:
        logger.error("PyYAML not installed. Run: pip install pyyaml")
        exit(1)
    
    # Start status watcher thread
    stop_watch = threading.Event()
    t = threading.Thread(target=watch_status_folder, args=(stop_watch,), daemon=True)
    t.start()
    logger.info("Started status watcher thread")

    try:
        with client:
            client.loop.run_until_complete(main())
            client.run_until_disconnected()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
    except Exception as e:
        logger.error(f"Fatal error in main execution: {e}", exc_info=True)
    finally:
        stop_watch.set()
        logger.info("Shutdown complete")
