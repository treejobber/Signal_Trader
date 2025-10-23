# telegram_harvester.py
# ---------------------
# Backfills recent Telegram channel messages and streams new ones to history.txt
# Adds:
#   - emit_command(cmd)  -> writes command JSONs to orders_out/  (Step C)
#   - status watcher     -> reads status_out/*.json and logs them (Step D)
# UPDATED: Added robust error handling for all file operations

import os, json, uuid, threading, time, re, logging
from pathlib import Path
from datetime import timezone
from typing import Optional, Dict, Any

from telethon import TelegramClient, events

# --- optional .env support (safe to ignore if not installed) ---
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
        logging.FileHandler('telegram_harvester.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)
# =========================================================

# ===================== CONFIG =====================
API_ID = int(os.getenv("API_ID", "0"))
if API_ID == 0:
    logger.error("API_ID not set in environment variables")
    raise ValueError("API_ID must be set in environment")

API_HASH = os.getenv("API_HASH", "")
if not API_HASH:
    logger.error("API_HASH not set in environment variables")
    raise ValueError("API_HASH must be set in environment")

SESSION_NAME = os.getenv("SESSION_NAME", "TelegramReader")
CHANNEL = os.getenv("CHANNEL", "@Sureshotfx_Signals_Free")
BACKFILL_LIMIT = int(os.getenv("BACKFILL_LIMIT", "100"))

# Files / folders
OUT_PATH = Path("history.txt")        # feed log (UTC ISO \t text)
ORDERS_DIR = Path("orders_out")       # where we drop commands for NT (Step C)
STATUS_DIR = Path("status_out")       # where NT drops status events (Step D)
PROCESSED_DIR = STATUS_DIR / "processed"
STATUS_LOG = Path("status_log.jsonl") # append-only log of status events

# Create directories with error handling
for p in (ORDERS_DIR, STATUS_DIR, PROCESSED_DIR):
    try:
        p.mkdir(exist_ok=True, parents=True)
        logger.info(f"Ensured directory exists: {p}")
    except Exception as e:
        logger.error(f"Failed to create directory {p}: {e}", exc_info=True)
        raise
# ==================================================

client = TelegramClient(SESSION_NAME, API_ID, API_HASH)

# ------------- STEP C: command emitter with robust error handling -------------
def emit_command(cmd: Dict[str, Any]) -> Optional[Path]:
    """
    Write a command JSON for NinjaTrader to pick up using atomic file operations.
    
    Example cmd:
      {
        "cmd": "OPEN",                # OPEN/MOVE_SL/MOVE_TP/CLOSE_PARTIAL/CLOSE_ALL/CANCEL_PENDING
        "signal": "sig_demo_1",       # your stable id per trade
        "trader": "Jason",
        "side": "BUY",                # BUY/SELL (for OPEN)
        "orderType": "LIMIT",         # MARKET/LIMIT/STOP (for OPEN)
        "price": 4258.44,             # optional for MARKET
        "stopLoss": 4250.40,          # optional
        "takeProfit": 4282.40,        # optional
        "qty": 1,                     # contracts
        "ntInstrument": "GC 12-25",   # Ninja instrument to trade
        "account": "Sim101"
      }
    
    Returns:
        Path to the written file, or None if write failed
    """
    try:
        # Ensure command has an ID
        if "id" not in cmd:
            cmd["id"] = str(uuid.uuid4())
        
        # Validate required fields
        if "cmd" not in cmd:
            logger.error(f"Command missing 'cmd' field: {cmd}")
            return None
        
        # Define final path
        final_path = ORDERS_DIR / f"CMD_{cmd['id']}.json"
        
        # Write to temporary file first (atomic operation)
        temp_path = final_path.with_suffix('.tmp')
        
        try:
            # Serialize to JSON
            json_content = json.dumps(cmd, ensure_ascii=False, indent=2)
        except (TypeError, ValueError) as e:
            logger.error(f"Failed to serialize command to JSON: {e}", exc_info=True)
            logger.error(f"Problematic command: {cmd}")
            return None
        
        try:
            # Write to temp file
            temp_path.write_text(json_content, encoding="utf-8")
            logger.debug(f"Wrote temporary file: {temp_path}")
        except IOError as e:
            logger.error(f"Failed to write temporary file {temp_path}: {e}", exc_info=True)
            return None
        
        try:
            # Atomic rename (on most systems)
            temp_path.rename(final_path)
            logger.info(f"[CMD] Wrote {final_path.name} ({cmd.get('cmd')}) for signal {cmd.get('signal')}")
            return final_path
        except OSError as e:
            logger.error(f"Failed to rename {temp_path} to {final_path}: {e}", exc_info=True)
            # Cleanup temp file if rename failed
            try:
                if temp_path.exists():
                    temp_path.unlink()
            except Exception as cleanup_error:
                logger.error(f"Failed to cleanup temp file {temp_path}: {cleanup_error}")
            return None
            
    except Exception as e:
        logger.error(f"Unexpected error in emit_command: {e}", exc_info=True)
        logger.error(f"Command that caused error: {cmd}")
        return None
# -----------------------------------------------------------------------------

# ------------- STEP D: status watcher with robust error handling -------------
def handle_status(evt: Dict[str, Any]) -> bool:
    """
    Called when a new status JSON appears in status_out/.
    Appends to status_log.jsonl and logs the event.
    
    Args:
        evt: Status event dictionary
        
    Returns:
        bool: True if successfully handled, False otherwise
    """
    try:
        # Validate event has required fields
        if not isinstance(evt, dict):
            logger.error(f"Status event is not a dictionary: {type(evt)}")
            return False
        
        evt_type = evt.get('evt', 'UNKNOWN')
        signal_id = evt.get('signal', 'UNKNOWN')
        
        # Serialize to JSON for logging
        try:
            json_line = json.dumps(evt, ensure_ascii=False)
        except (TypeError, ValueError) as e:
            logger.error(f"Failed to serialize status event to JSON: {e}", exc_info=True)
            logger.error(f"Problematic event: {evt}")
            return False
        
        # Append to status log file
        try:
            with STATUS_LOG.open("a", encoding="utf-8") as f:
                f.write(json_line + "\n")
        except IOError as e:
            logger.error(f"Failed to write to status log {STATUS_LOG}: {e}", exc_info=True)
            return False
        
        logger.info(f"[STAT] {evt_type} for signal={signal_id} -> {evt}")
        return True
        
    except Exception as e:
        logger.error(f"Unexpected error in handle_status: {e}", exc_info=True)
        logger.error(f"Event that caused error: {evt}")
        return False

def watch_status_folder(stop_event: threading.Event):
    """
    Poll status_out/ for new *.json files and process them with error handling.
    NT should write files like:
      {"evt":"FILLED","signal":"sig_demo_1","avgFill":4258.40,"qtyFilled":1,"side":"BUY"}
    """
    seen = set()
    logger.info("Status watcher thread started")
    
    while not stop_event.is_set():
        try:
            # List all JSON files in status directory
            json_files = list(STATUS_DIR.glob("*.json"))
            
            for p in json_files:
                if p.name in seen:
                    continue
                
                try:
                    # Read the file
                    try:
                        content = p.read_text(encoding="utf-8")
                    except IOError as e:
                        logger.error(f"Failed to read status file {p.name}: {e}")
                        # Don't mark as seen so we can retry
                        continue
                    
                    # Parse JSON
                    try:
                        data = json.loads(content)
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse JSON in {p.name}: {e}")
                        logger.error(f"Content: {content[:200]}")  # Log first 200 chars
                        # Mark as seen to avoid infinite retries on corrupt files
                        seen.add(p.name)
                        # Try to move to processed anyway to clear it
                        try:
                            corrupted_path = PROCESSED_DIR / f"CORRUPT_{p.name}"
                            p.rename(corrupted_path)
                            logger.info(f"Moved corrupted file to {corrupted_path}")
                        except Exception as move_error:
                            logger.error(f"Failed to move corrupted file {p.name}: {move_error}")
                        continue
                    
                    # Handle the status
                    if handle_status(data):
                        seen.add(p.name)
                        
                        # Archive to /processed
                        try:
                            dest_path = PROCESSED_DIR / p.name
                            p.rename(dest_path)
                            logger.debug(f"Moved {p.name} to processed/")
                        except OSError as e:
                            logger.error(f"Failed to move {p.name} to processed/: {e}")
                            # File was processed but couldn't be moved
                            # Still mark as seen to avoid reprocessing
                    else:
                        logger.warning(f"Failed to handle status from {p.name}, will retry")
                        
                except Exception as e:
                    logger.error(f"Error processing status file {p.name}: {e}", exc_info=True)
                    # Don't mark as seen so we can retry
                    
        except Exception as e:
            logger.error(f"Error in status watcher main loop: {e}", exc_info=True)
        
        time.sleep(0.5)
    
    logger.info("Status watcher thread stopped")
# -----------------------------------------------------------------------------

# ----------------- Telegram logic with error handling ------------------
async def fetch_history():
    """
    Fetch the last BACKFILL_LIMIT messages using Telethon's high-level iterator
    and write them oldest->newest to history.txt with error handling.
    """
    try:
        channel = await client.get_entity(CHANNEL)
        logger.info(f"Connected to channel: {CHANNEL}")
    except Exception as e:
        logger.error(f"Failed to get Telegram channel {CHANNEL}: {e}", exc_info=True)
        return
    
    msgs = []
    try:
        async for m in client.iter_messages(channel, limit=BACKFILL_LIMIT):
            if m.message:
                msgs.append(m)
    except Exception as e:
        logger.error(f"Error fetching message history: {e}", exc_info=True)
        if not msgs:
            return  # No messages collected
        logger.warning(f"Partial history fetched: {len(msgs)} messages")
    
    # Write oldest → newest for readability
    try:
        with OUT_PATH.open("w", encoding="utf-8") as out:
            for message in reversed(msgs):
                try:
                    # Telethon datetimes are tz-aware; normalize to UTC ISO
                    iso_utc = message.date.astimezone(timezone.utc).isoformat()
                    text_one_line = message.message.replace("\n", " ").strip()
                    out.write(f"{iso_utc}\t{text_one_line}\n")
                except Exception as e:
                    logger.error(f"Error processing message {message.id}: {e}")
                    continue  # Skip this message but continue with others
        
        logger.info(f"[INIT] Saved the last {len(msgs)} messages to {OUT_PATH.name}")
    except IOError as e:
        logger.error(f"Failed to write history file {OUT_PATH}: {e}", exc_info=True)

@client.on(events.NewMessage(chats=[CHANNEL]))
async def on_new_message(event):
    """
    Append each new post as it arrives with error handling.
    (We keep this simple for now; later we'll parse & correlate.)
    """
    try:
        text = event.raw_text.replace("\n", " ").strip()
        iso_utc = event.message.date.astimezone(timezone.utc).isoformat()

        # Append to history file
        try:
            with OUT_PATH.open("a", encoding="utf-8") as out:
                out.write(f"{iso_utc}\t{text}\n")
        except IOError as e:
            logger.error(f"Failed to append to history file {OUT_PATH}: {e}", exc_info=True)
            # Continue anyway - we'll log but not crash

        logger.info(f"[NEW] {iso_utc}  {text[:120]}")
        
    except Exception as e:
        logger.error(f"Error processing new message: {e}", exc_info=True)

async def main():
    """Main entry point with error handling"""
    try:
        # Ensure history file exists
        if not OUT_PATH.exists():
            try:
                OUT_PATH.touch()
                logger.info(f"Created history file: {OUT_PATH}")
            except IOError as e:
                logger.error(f"Failed to create history file {OUT_PATH}: {e}", exc_info=True)
                raise
        
        logger.info(f"[OK] Monitoring channel: {CHANNEL}")
        
        if BACKFILL_LIMIT > 0:
            await fetch_history()
        
        logger.info("[READY] Live monitoring… (Ctrl+C to stop)")
        
    except Exception as e:
        logger.error(f"Error in main(): {e}", exc_info=True)
        raise

# ---------------------- run ------------------------
if __name__ == "__main__":
    # start status watcher thread
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