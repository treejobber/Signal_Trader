"""
test_database.py
----------------
Quick test script to verify database integration is working
Run this to ensure database.py is functioning correctly
"""

import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

def test_database():
    """Test database creation and basic operations"""
    
    print("🧪 Testing Signal_Trader Database Integration")
    print("=" * 60)
    print()
    
    # Test 1: Import database module
    print("Test 1: Importing database module...")
    try:
        from database import TradingDatabase
        print("✅ SUCCESS: database.py imported successfully")
    except ImportError as e:
        print(f"❌ FAILED: Could not import database.py: {e}")
        return False
    print()
    
    # Test 2: Create database instance
    print("Test 2: Creating database instance...")
    try:
        db = TradingDatabase("test_trading.db")
        print("✅ SUCCESS: Database instance created")
        print(f"   Location: {db.db_path}")
    except Exception as e:
        print(f"❌ FAILED: Could not create database: {e}")
        return False
    print()
    
    # Test 3: Insert test signal
    print("Test 3: Inserting test signal...")
    try:
        result = db.insert_signal("sig_test_001", {
            'channel': '@TestChannel',
            'raw_text': 'XAUUSD BUY 4258.44 SL: 4250.40 TP: 4282.40 --Trade by TestBot',
            'symbol': 'XAUUSD',
            'side': 'BUY',
            'entry_price': 4258.44,
            'stop_loss': 4250.40,
            'take_profit': 4282.40,
            'trader': 'TestBot'
        })
        if result:
            print("✅ SUCCESS: Test signal inserted")
        else:
            print("❌ FAILED: Signal insertion returned False")
            return False
    except Exception as e:
        print(f"❌ FAILED: Could not insert signal: {e}")
        return False
    print()
    
    # Test 4: Insert test order
    print("Test 4: Inserting test order...")
    try:
        result = db.insert_order("ord_test_001", "sig_test_001", {
            'cmd': 'OPEN',
            'ntInstrument': 'GC 12-25',
            'side': 'BUY',
            'orderType': 'MARKET',
            'qty': 1,
            'price': 4258.44,
            'stopLoss': 4250.40,
            'takeProfit': 4282.40,
            'account': 'Sim101'
        })
        if result:
            print("✅ SUCCESS: Test order inserted")
        else:
            print("❌ FAILED: Order insertion returned False")
            return False
    except Exception as e:
        print(f"❌ FAILED: Could not insert order: {e}")
        return False
    print()
    
    # Test 5: Insert test execution
    print("Test 5: Inserting test execution...")
    try:
        result = db.insert_execution("sig_test_001", {
            'executionId': 'exec_test_001',
            'orderId': 'ord_test_001',
            'evt': 'FILLED',
            'instrument': 'GC 12-25',
            'side': 'BUY',
            'avgFill': 4258.50,
            'qtyFilled': 1,
            'status': 'FILLED'
        })
        if result:
            print("✅ SUCCESS: Test execution inserted")
        else:
            print("❌ FAILED: Execution insertion returned False")
            return False
    except Exception as e:
        print(f"❌ FAILED: Could not insert execution: {e}")
        return False
    print()
    
    # Test 6: Query recent signals
    print("Test 6: Querying recent signals...")
    try:
        signals = db.get_recent_signals(limit=10)
        print(f"✅ SUCCESS: Retrieved {len(signals)} signals")
        if signals:
            print(f"   First signal: {signals[0].get('signal_id')} - {signals[0].get('symbol')} {signals[0].get('side')}")
    except Exception as e:
        print(f"❌ FAILED: Could not query signals: {e}")
        return False
    print()
    
    # Test 7: Get stats summary
    print("Test 7: Getting stats summary...")
    try:
        stats = db.get_stats_summary()
        print("✅ SUCCESS: Retrieved stats")
        print(f"   Total trades: {stats.get('total_trades', 0)}")
        print(f"   Win rate: {stats.get('win_rate', 0):.1f}%")
        print(f"   Total P&L: ${stats.get('total_pnl', 0):.2f}")
    except Exception as e:
        print(f"❌ FAILED: Could not get stats: {e}")
        return False
    print()
    
    # Test 8: Get signal history
    print("Test 8: Getting signal history...")
    try:
        history = db.get_signal_history("sig_test_001")
        print("✅ SUCCESS: Retrieved signal history")
        print(f"   Signal: {history.get('signal', {}).get('signal_id', 'None')}")
        print(f"   Orders: {len(history.get('orders', []))}")
        print(f"   Executions: {len(history.get('executions', []))}")
    except Exception as e:
        print(f"❌ FAILED: Could not get signal history: {e}")
        return False
    print()
    
    # Cleanup
    print("Cleaning up...")
    try:
        Path("test_trading.db").unlink()
        print("✅ Test database deleted")
    except Exception as e:
        print(f"⚠️  Could not delete test database: {e}")
    print()
    
    return True


def main():
    """Run all tests"""
    print()
    success = test_database()
    print()
    print("=" * 60)
    if success:
        print("🎉 ALL TESTS PASSED!")
        print()
        print("Your database integration is working correctly.")
        print("You can now:")
        print("  1. Run telegram_harvester.py to start collecting real data")
        print("  2. Install Grafana and connect to trading.db")
        print("  3. Create your dashboard using the SQL queries in GRAFANA_SETUP.md")
    else:
        print("❌ SOME TESTS FAILED")
        print()
        print("Please check:")
        print("  1. database.py is in the same directory as this script")
        print("  2. You have write permissions in this directory")
        print("  3. Check error messages above for details")
    print("=" * 60)
    print()
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())