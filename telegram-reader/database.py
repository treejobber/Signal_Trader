"""
database.py
-----------
SQLite database layer for Signal_Trader
Stores all signals, orders, and executions for Grafana visualization
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Any
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)

class TradingDatabase:
    """
    Manages SQLite database for trading signals and executions.
    Designed for Grafana time-series visualization.
    """
    
    def __init__(self, db_path: str = "trading.db"):
        self.db_path = Path(db_path)
        self._init_schema()
        logger.info(f"Trading database initialized at {self.db_path}")
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {e}", exc_info=True)
            raise
        finally:
            conn.close()
    
    def _init_schema(self):
        """Create database tables if they don't exist"""
        with self.get_connection() as conn:
            conn.executescript("""
                -- Signals table: Raw signals from Telegram
                CREATE TABLE IF NOT EXISTS signals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    signal_id TEXT UNIQUE NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    channel TEXT,
                    raw_text TEXT,
                    symbol TEXT,
                    side TEXT,
                    entry_price REAL,
                    stop_loss REAL,
                    take_profit REAL,
                    trader TEXT,
                    status TEXT DEFAULT 'pending',
                    notes TEXT
                );
                
                -- Orders table: Commands sent to NinjaTrader
                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id TEXT UNIQUE NOT NULL,
                    signal_id TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    command_type TEXT,
                    symbol TEXT,
                    side TEXT,
                    order_type TEXT,
                    quantity INTEGER,
                    price REAL,
                    stop_loss REAL,
                    take_profit REAL,
                    account TEXT,
                    status TEXT DEFAULT 'pending',
                    FOREIGN KEY(signal_id) REFERENCES signals(signal_id)
                );
                
                -- Executions table: Trade fills from NinjaTrader
                CREATE TABLE IF NOT EXISTS executions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    execution_id TEXT,
                    order_id TEXT,
                    signal_id TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    event_type TEXT,
                    symbol TEXT,
                    side TEXT,
                    fill_price REAL,
                    quantity_filled INTEGER,
                    status TEXT,
                    commission REAL,
                    raw_data TEXT,
                    FOREIGN KEY(order_id) REFERENCES orders(order_id),
                    FOREIGN KEY(signal_id) REFERENCES signals(signal_id)
                );
                
                -- Positions table: Active trading positions
                CREATE TABLE IF NOT EXISTS positions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    position_id TEXT UNIQUE NOT NULL,
                    signal_id TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    symbol TEXT,
                    side TEXT,
                    entry_price REAL,
                    quantity INTEGER,
                    stop_loss REAL,
                    take_profit REAL,
                    current_price REAL,
                    unrealized_pnl REAL,
                    status TEXT DEFAULT 'open',
                    closed_at DATETIME,
                    realized_pnl REAL,
                    FOREIGN KEY(signal_id) REFERENCES signals(signal_id)
                );
                
                -- Performance metrics table: Aggregated stats
                CREATE TABLE IF NOT EXISTS performance_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    metric_type TEXT,
                    metric_name TEXT,
                    metric_value REAL,
                    period TEXT,
                    channel TEXT
                );
                
                -- System health table: Monitoring data
                CREATE TABLE IF NOT EXISTS system_health (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    component TEXT,
                    status TEXT,
                    latency_ms INTEGER,
                    error_count INTEGER,
                    message TEXT
                );
                
                -- Create indexes for performance
                CREATE INDEX IF NOT EXISTS idx_signals_timestamp ON signals(timestamp);
                CREATE INDEX IF NOT EXISTS idx_signals_status ON signals(status);
                CREATE INDEX IF NOT EXISTS idx_signals_channel ON signals(channel);
                
                CREATE INDEX IF NOT EXISTS idx_orders_timestamp ON orders(timestamp);
                CREATE INDEX IF NOT EXISTS idx_orders_signal ON orders(signal_id);
                CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
                
                CREATE INDEX IF NOT EXISTS idx_executions_timestamp ON executions(timestamp);
                CREATE INDEX IF NOT EXISTS idx_executions_signal ON executions(signal_id);
                
                CREATE INDEX IF NOT EXISTS idx_positions_status ON positions(status);
                CREATE INDEX IF NOT EXISTS idx_positions_signal ON positions(signal_id);
                
                CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON performance_metrics(timestamp);
                CREATE INDEX IF NOT EXISTS idx_health_timestamp ON system_health(timestamp);
            """)
        logger.info("Database schema initialized successfully")
    
    # ==================== SIGNAL OPERATIONS ====================
    
    def insert_signal(self, signal_id: str, data: Dict[str, Any]) -> bool:
        """Insert a new signal from Telegram"""
        try:
            with self.get_connection() as conn:
                conn.execute("""
                    INSERT INTO signals (
                        signal_id, channel, raw_text, symbol, side, 
                        entry_price, stop_loss, take_profit, trader, status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    signal_id,
                    data.get('channel', ''),
                    data.get('raw_text', ''),
                    data.get('symbol', ''),
                    data.get('side', ''),
                    data.get('entry_price'),
                    data.get('stop_loss'),
                    data.get('take_profit'),
                    data.get('trader', ''),
                    data.get('status', 'pending')
                ))
            logger.info(f"Signal {signal_id} inserted successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to insert signal {signal_id}: {e}")
            return False
    
    def update_signal_status(self, signal_id: str, status: str, notes: str = None) -> bool:
        """Update signal status"""
        try:
            with self.get_connection() as conn:
                conn.execute("""
                    UPDATE signals 
                    SET status = ?, notes = ?
                    WHERE signal_id = ?
                """, (status, notes, signal_id))
            logger.debug(f"Signal {signal_id} status updated to {status}")
            return True
        except Exception as e:
            logger.error(f"Failed to update signal {signal_id}: {e}")
            return False
    
    # ==================== ORDER OPERATIONS ====================
    
    def insert_order(self, order_id: str, signal_id: str, data: Dict[str, Any]) -> bool:
        """Insert an order sent to NinjaTrader"""
        try:
            with self.get_connection() as conn:
                conn.execute("""
                    INSERT INTO orders (
                        order_id, signal_id, command_type, symbol, side,
                        order_type, quantity, price, stop_loss, take_profit,
                        account, status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    order_id,
                    signal_id,
                    data.get('cmd', 'OPEN'),
                    data.get('ntInstrument', ''),
                    data.get('side', ''),
                    data.get('orderType', 'MARKET'),
                    data.get('qty', 1),
                    data.get('price'),
                    data.get('stopLoss'),
                    data.get('takeProfit'),
                    data.get('account', ''),
                    'sent'
                ))
            logger.info(f"Order {order_id} inserted successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to insert order {order_id}: {e}")
            return False
    
    def update_order_status(self, order_id: str, status: str) -> bool:
        """Update order status"""
        try:
            with self.get_connection() as conn:
                conn.execute("""
                    UPDATE orders 
                    SET status = ?
                    WHERE order_id = ?
                """, (status, order_id))
            return True
        except Exception as e:
            logger.error(f"Failed to update order {order_id}: {e}")
            return False
    
    # ==================== EXECUTION OPERATIONS ====================
    
    def insert_execution(self, signal_id: str, data: Dict[str, Any]) -> bool:
        """Insert an execution from NinjaTrader"""
        try:
            with self.get_connection() as conn:
                conn.execute("""
                    INSERT INTO executions (
                        execution_id, order_id, signal_id, event_type,
                        symbol, side, fill_price, quantity_filled,
                        status, raw_data
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    data.get('executionId', ''),
                    data.get('orderId', ''),
                    signal_id,
                    data.get('evt', ''),
                    data.get('instrument', ''),
                    data.get('side', ''),
                    data.get('avgFill'),
                    data.get('qtyFilled', 0),
                    data.get('status', ''),
                    json.dumps(data)
                ))
            logger.info(f"Execution for signal {signal_id} inserted")
            return True
        except Exception as e:
            logger.error(f"Failed to insert execution: {e}")
            return False
    
    # ==================== POSITION OPERATIONS ====================
    
    def insert_position(self, position_id: str, signal_id: str, data: Dict[str, Any]) -> bool:
        """Insert a new position"""
        try:
            with self.get_connection() as conn:
                conn.execute("""
                    INSERT INTO positions (
                        position_id, signal_id, symbol, side, entry_price,
                        quantity, stop_loss, take_profit, current_price,
                        unrealized_pnl, status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    position_id,
                    signal_id,
                    data.get('symbol', ''),
                    data.get('side', ''),
                    data.get('entry_price'),
                    data.get('quantity', 1),
                    data.get('stop_loss'),
                    data.get('take_profit'),
                    data.get('current_price'),
                    data.get('unrealized_pnl', 0.0),
                    'open'
                ))
            logger.info(f"Position {position_id} opened")
            return True
        except Exception as e:
            logger.error(f"Failed to insert position: {e}")
            return False
    
    def close_position(self, position_id: str, realized_pnl: float) -> bool:
        """Close a position"""
        try:
            with self.get_connection() as conn:
                conn.execute("""
                    UPDATE positions 
                    SET status = 'closed',
                        closed_at = CURRENT_TIMESTAMP,
                        realized_pnl = ?
                    WHERE position_id = ?
                """, (realized_pnl, position_id))
            logger.info(f"Position {position_id} closed with P&L: {realized_pnl}")
            return True
        except Exception as e:
            logger.error(f"Failed to close position: {e}")
            return False
    
    # ==================== METRICS OPERATIONS ====================
    
    def log_metric(self, metric_type: str, metric_name: str, value: float, 
                   period: str = 'realtime', channel: str = None) -> bool:
        """Log a performance metric"""
        try:
            with self.get_connection() as conn:
                conn.execute("""
                    INSERT INTO performance_metrics (
                        metric_type, metric_name, metric_value, period, channel
                    ) VALUES (?, ?, ?, ?, ?)
                """, (metric_type, metric_name, value, period, channel))
            return True
        except Exception as e:
            logger.error(f"Failed to log metric: {e}")
            return False
    
    def log_health(self, component: str, status: str, latency_ms: int = None,
                   error_count: int = 0, message: str = None) -> bool:
        """Log system health data"""
        try:
            with self.get_connection() as conn:
                conn.execute("""
                    INSERT INTO system_health (
                        component, status, latency_ms, error_count, message
                    ) VALUES (?, ?, ?, ?, ?)
                """, (component, status, latency_ms, error_count, message))
            return True
        except Exception as e:
            logger.error(f"Failed to log health: {e}")
            return False
    
    # ==================== QUERY OPERATIONS ====================
    
    def get_active_positions(self) -> List[Dict[str, Any]]:
        """Get all open positions"""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT * FROM positions 
                    WHERE status = 'open'
                    ORDER BY timestamp DESC
                """)
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Failed to get active positions: {e}")
            return []
    
    def get_recent_signals(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent signals"""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT * FROM signals 
                    ORDER BY timestamp DESC
                    LIMIT ?
                """, (limit,))
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Failed to get recent signals: {e}")
            return []
    
    def get_signal_history(self, signal_id: str) -> Dict[str, Any]:
        """Get complete history for a signal"""
        try:
            with self.get_connection() as conn:
                signal = conn.execute(
                    "SELECT * FROM signals WHERE signal_id = ?", (signal_id,)
                ).fetchone()
                
                orders = conn.execute(
                    "SELECT * FROM orders WHERE signal_id = ? ORDER BY timestamp",
                    (signal_id,)
                ).fetchall()
                
                executions = conn.execute(
                    "SELECT * FROM executions WHERE signal_id = ? ORDER BY timestamp",
                    (signal_id,)
                ).fetchall()
                
                position = conn.execute(
                    "SELECT * FROM positions WHERE signal_id = ?",
                    (signal_id,)
                ).fetchone()
                
                return {
                    'signal': dict(signal) if signal else None,
                    'orders': [dict(order) for order in orders],
                    'executions': [dict(ex) for ex in executions],
                    'position': dict(position) if position else None
                }
        except Exception as e:
            logger.error(f"Failed to get signal history: {e}")
            return {}
    
    def get_daily_pnl(self, days: int = 30) -> List[Dict[str, Any]]:
        """Get daily P&L for last N days"""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT 
                        DATE(closed_at) as date,
                        COUNT(*) as trades,
                        SUM(CASE WHEN realized_pnl > 0 THEN 1 ELSE 0 END) as wins,
                        SUM(realized_pnl) as total_pnl,
                        AVG(realized_pnl) as avg_pnl
                    FROM positions
                    WHERE status = 'closed'
                        AND closed_at >= datetime('now', '-' || ? || ' days')
                    GROUP BY DATE(closed_at)
                    ORDER BY date DESC
                """, (days,))
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Failed to get daily P&L: {e}")
            return []
    
    def get_stats_summary(self) -> Dict[str, Any]:
        """Get overall trading statistics"""
        try:
            with self.get_connection() as conn:
                # Total trades
                total = conn.execute(
                    "SELECT COUNT(*) as count FROM positions WHERE status = 'closed'"
                ).fetchone()
                
                # Win rate
                wins = conn.execute(
                    "SELECT COUNT(*) as count FROM positions WHERE status = 'closed' AND realized_pnl > 0"
                ).fetchone()
                
                # Total P&L
                pnl = conn.execute(
                    "SELECT SUM(realized_pnl) as total FROM positions WHERE status = 'closed'"
                ).fetchone()
                
                # Active positions
                active = conn.execute(
                    "SELECT COUNT(*) as count FROM positions WHERE status = 'open'"
                ).fetchone()
                
                total_count = total['count'] if total else 0
                win_count = wins['count'] if wins else 0
                
                return {
                    'total_trades': total_count,
                    'winning_trades': win_count,
                    'losing_trades': total_count - win_count,
                    'win_rate': (win_count / total_count * 100) if total_count > 0 else 0,
                    'total_pnl': pnl['total'] if pnl and pnl['total'] else 0,
                    'active_positions': active['count'] if active else 0
                }
        except Exception as e:
            logger.error(f"Failed to get stats summary: {e}")
            return {}


# Global database instance
db = None

def get_db(db_path: str = "trading.db") -> TradingDatabase:
    """Get or create database instance"""
    global db
    if db is None:
        db = TradingDatabase(db_path)
    return db


if __name__ == "__main__":
    # Test the database
    logging.basicConfig(level=logging.INFO)
    
    test_db = TradingDatabase("test_trading.db")
    
    # Insert test signal
    test_db.insert_signal("sig_test_001", {
        'channel': '@TestChannel',
        'raw_text': 'XAUUSD BUY 4258.44 SL: 4250.40 TP: 4282.40',
        'symbol': 'XAUUSD',
        'side': 'BUY',
        'entry_price': 4258.44,
        'stop_loss': 4250.40,
        'take_profit': 4282.40,
        'trader': 'Jason'
    })
    
    # Get stats
    stats = test_db.get_stats_summary()
    print(f"Stats: {stats}")
    
    print("✅ Database test completed successfully")