import datetime
import yaml
import logging

# Setup logging
logger = logging.getLogger(__name__)

class LoggerPlugin:
    name = 'logger'
    
    def __init__(self, cfg: dict):
        """Initialize logger plugin"""
        try:
            self.commands = {'write': self.write}
            logger.info("LoggerPlugin initialized")
        except Exception as e:
            logger.error(f"Failed to initialize LoggerPlugin: {e}", exc_info=True)
            raise
    
    def write(self, p: dict) -> dict:
        """
        Write a log message with validation and error handling.
        
        Args:
            p: Parameters dictionary with 'level' and 'message' fields
            
        Returns:
            dict with logging result
        """
        try:
            # Validate input
            if not isinstance(p, dict):
                error_msg = f"Parameters must be a dictionary, got {type(p)}"
                logger.error(error_msg)
                return {
                    'logged': False,
                    'error': error_msg
                }
            
            # Extract and validate level
            level = str(p.get('level', 'INFO')).upper()
            valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
            
            if level not in valid_levels:
                logger.warning(f"Invalid log level '{level}', defaulting to INFO")
                level = 'INFO'
            
            # Extract message
            message = p.get('message', '')
            if not message:
                logger.warning("Empty log message received")
                message = "(empty message)"
            
            # Convert to string safely
            try:
                msg = str(message)
            except Exception as e:
                logger.error(f"Failed to convert message to string: {e}")
                msg = f"(unconvertible message: {type(message)})"
            
            # Generate timestamp
            try:
                ts = datetime.datetime.utcnow().isoformat()
            except Exception as e:
                logger.error(f"Failed to generate timestamp: {e}")
                ts = "UNKNOWN"
            
            # Format log line
            line = f'[{ts}] {level}: {msg}'
            
            # Print to console with flush
            try:
                print(line, flush=True)
            except Exception as e:
                # If print fails, log to python logger
                logger.error(f"Failed to print log line: {e}", exc_info=True)
            
            # Also log using Python's logging system
            try:
                python_logger = logging.getLogger('mcp.plugin.logger')
                log_func = getattr(python_logger, level.lower(), python_logger.info)
                log_func(msg)
            except Exception as e:
                logger.error(f"Failed to write to Python logger: {e}", exc_info=True)
            
            return {
                'logged': True,
                'level': level,
                'message': msg,
                'timestamp': ts
            }
            
        except Exception as e:
            error_msg = f"Unexpected error in LoggerPlugin.write: {e}"
            logger.error(error_msg, exc_info=True)
            return {
                'logged': False,
                'error': error_msg
            }

def _cfg():
    """Load configuration with error handling"""
    try:
        with open('./config/server_config.yaml', 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        logger.warning("Configuration file not found, using defaults")
        return {}
    except yaml.YAMLError as e:
        logger.error(f"Failed to parse YAML configuration: {e}", exc_info=True)
        return {}
    except Exception as e:
        logger.error(f"Unexpected error loading configuration: {e}", exc_info=True)
        return {}

PLUGIN = LoggerPlugin(_cfg())
