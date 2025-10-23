from pathlib import Path
import json, time, uuid, yaml, logging

# Setup logging
logger = logging.getLogger(__name__)

class TradeBridgePlugin:
    name = 'trade'
    
    def __init__(self, cfg: dict):
        try:
            base_dir = Path(cfg.get('storage', {}).get('base_dir', '.')).resolve()
            self.out_dir = (base_dir / cfg.get('storage', {}).get('orders_out_dir', './data/orders_out')).resolve()
            
            # Create output directory with error handling
            try:
                self.out_dir.mkdir(parents=True, exist_ok=True)
                logger.info(f"Trade bridge output directory: {self.out_dir}")
            except Exception as e:
                logger.error(f"Failed to create output directory {self.out_dir}: {e}", exc_info=True)
                raise
            
            self.commands = {
                'open': self.open_order,
                'close': self.close_order,
                'modify_sl_tp': self.modify_sl_tp
            }
            
        except Exception as e:
            logger.error(f"Failed to initialize TradeBridgePlugin: {e}", exc_info=True)
            raise
    
    def _write(self, payload: dict) -> dict:
        """
        Write command payload to file with atomic operation and error handling.
        
        Args:
            payload: Command dictionary to write
            
        Returns:
            dict with 'file' path and 'payload' content, or error info
        """
        try:
            # Generate filename
            ts = time.strftime('%Y%m%d_%H%M%S')
            uid = uuid.uuid4().hex[:8]
            filename = f'CMD_{ts}_{uid}.json'
            final_path = self.out_dir / filename
            temp_path = self.out_dir / f'{filename}.tmp'
            
            # Validate payload
            if not isinstance(payload, dict):
                error_msg = f"Payload must be a dictionary, got {type(payload)}"
                logger.error(error_msg)
                return {'error': error_msg, 'success': False}
            
            # Serialize to JSON
            try:
                json_content = json.dumps(payload, indent=2)
            except (TypeError, ValueError) as e:
                error_msg = f"Failed to serialize payload to JSON: {e}"
                logger.error(error_msg, exc_info=True)
                return {'error': error_msg, 'success': False}
            
            # Write to temporary file first (atomic operation)
            try:
                with open(temp_path, 'w', encoding='utf-8') as f:
                    f.write(json_content)
                logger.debug(f"Wrote temporary file: {temp_path}")
            except IOError as e:
                error_msg = f"Failed to write temporary file {temp_path}: {e}"
                logger.error(error_msg, exc_info=True)
                return {'error': error_msg, 'success': False}
            
            # Atomic rename
            try:
                temp_path.rename(final_path)
                logger.info(f"Successfully wrote command file: {final_path}")
                return {
                    'file': str(final_path),
                    'payload': payload,
                    'success': True
                }
            except OSError as e:
                error_msg = f"Failed to rename {temp_path} to {final_path}: {e}"
                logger.error(error_msg, exc_info=True)
                
                # Cleanup temp file
                try:
                    if temp_path.exists():
                        temp_path.unlink()
                except Exception as cleanup_error:
                    logger.error(f"Failed to cleanup temp file {temp_path}: {cleanup_error}")
                
                return {'error': error_msg, 'success': False}
                
        except Exception as e:
            error_msg = f"Unexpected error in _write: {e}"
            logger.error(error_msg, exc_info=True)
            return {'error': error_msg, 'success': False}
    
    def open_order(self, p: dict) -> dict:
        """
        Create an OPEN order command with validation.
        
        Args:
            p: Parameters dictionary
            
        Returns:
            Result of write operation
        """
        try:
            # Build command with defaults and validation
            d = {
                'cmd': 'OPEN',
                'signal': p.get('signal', uuid.uuid4().hex),
                'symbol': p.get('symbol', 'GC'),
                'side': str(p.get('side', 'BUY')).upper(),
                'orderType': str(p.get('orderType', 'MARKET')).upper(),
                'qty': int(p.get('qty', 1))
            }
            
            # Validate side
            if d['side'] not in ['BUY', 'SELL']:
                error_msg = f"Invalid side: {d['side']}, must be BUY or SELL"
                logger.error(error_msg)
                return {'error': error_msg, 'success': False}
            
            # Validate order type
            if d['orderType'] not in ['MARKET', 'LIMIT', 'STOP', 'STOP_LIMIT']:
                error_msg = f"Invalid orderType: {d['orderType']}"
                logger.error(error_msg)
                return {'error': error_msg, 'success': False}
            
            # Validate quantity
            if d['qty'] <= 0:
                error_msg = f"Invalid quantity: {d['qty']}, must be positive"
                logger.error(error_msg)
                return {'error': error_msg, 'success': False}
            
            # Add optional fields with validation
            for k in ('price', 'stopLoss', 'takeProfit'):
                if k in p:
                    try:
                        value = float(p[k])
                        if value <= 0:
                            logger.warning(f"Invalid {k}: {value}, must be positive. Skipping.")
                        else:
                            d[k] = value
                    except (TypeError, ValueError) as e:
                        logger.warning(f"Failed to convert {k} to float: {e}. Skipping.")
            
            logger.info(f"Creating OPEN order: signal={d['signal']}, side={d['side']}, qty={d['qty']}")
            return self._write(d)
            
        except Exception as e:
            error_msg = f"Error in open_order: {e}"
            logger.error(error_msg, exc_info=True)
            return {'error': error_msg, 'success': False}
    
    def close_order(self, p: dict) -> dict:
        """
        Create a CLOSE order command.
        
        Args:
            p: Parameters dictionary with 'signal' field required
            
        Returns:
            Result of write operation
        """
        try:
            signal = p.get('signal')
            if not signal:
                error_msg = "Missing required 'signal' parameter for close_order"
                logger.error(error_msg)
                return {'error': error_msg, 'success': False}
            
            d = {
                'cmd': 'CLOSE',
                'signal': signal
            }
            
            logger.info(f"Creating CLOSE order: signal={signal}")
            return self._write(d)
            
        except Exception as e:
            error_msg = f"Error in close_order: {e}"
            logger.error(error_msg, exc_info=True)
            return {'error': error_msg, 'success': False}
    
    def modify_sl_tp(self, p: dict) -> dict:
        """
        Create a MODIFY command to update stop loss and/or take profit.
        
        Args:
            p: Parameters dictionary with 'signal' and at least one of 'stopLoss' or 'takeProfit'
            
        Returns:
            Result of write operation
        """
        try:
            signal = p.get('signal')
            if not signal:
                error_msg = "Missing required 'signal' parameter for modify_sl_tp"
                logger.error(error_msg)
                return {'error': error_msg, 'success': False}
            
            d = {
                'cmd': 'MODIFY',
                'signal': signal
            }
            
            # Add stop loss if provided
            if 'stopLoss' in p:
                try:
                    sl = float(p['stopLoss'])
                    if sl <= 0:
                        logger.warning(f"Invalid stopLoss: {sl}, must be positive. Skipping.")
                    else:
                        d['stopLoss'] = sl
                except (TypeError, ValueError) as e:
                    logger.warning(f"Failed to convert stopLoss to float: {e}. Skipping.")
            
            # Add take profit if provided
            if 'takeProfit' in p:
                try:
                    tp = float(p['takeProfit'])
                    if tp <= 0:
                        logger.warning(f"Invalid takeProfit: {tp}, must be positive. Skipping.")
                    else:
                        d['takeProfit'] = tp
                except (TypeError, ValueError) as e:
                    logger.warning(f"Failed to convert takeProfit to float: {e}. Skipping.")
            
            # Ensure at least one modification was added
            if 'stopLoss' not in d and 'takeProfit' not in d:
                error_msg = "No valid stopLoss or takeProfit provided for modify_sl_tp"
                logger.error(error_msg)
                return {'error': error_msg, 'success': False}
            
            logger.info(f"Creating MODIFY order: signal={signal}")
            return self._write(d)
            
        except Exception as e:
            error_msg = f"Error in modify_sl_tp: {e}"
            logger.error(error_msg, exc_info=True)
            return {'error': error_msg, 'success': False}

def _cfg():
    """Load configuration with error handling"""
    try:
        with open('./config/server_config.yaml', 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        logger.error("Configuration file not found: ./config/server_config.yaml")
        # Return minimal default config
        return {
            'storage': {
                'base_dir': '.',
                'orders_out_dir': './data/orders_out'
            }
        }
    except yaml.YAMLError as e:
        logger.error(f"Failed to parse YAML configuration: {e}", exc_info=True)
        raise
    except Exception as e:
        logger.error(f"Unexpected error loading configuration: {e}", exc_info=True)
        raise

PLUGIN = TradeBridgePlugin(_cfg())
