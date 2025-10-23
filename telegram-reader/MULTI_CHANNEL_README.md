# Multi-Channel Telegram Harvester

## 🎉 New Features

- ✅ Monitor **10+ channels simultaneously**
- ✅ Individual settings per channel
- ✅ Per-channel history files
- ✅ Channel-specific parsers
- ✅ Risk management per channel
- ✅ Easy channel management via YAML config

---

## 📋 Setup

### 1. Install PyYAML

```bash
pip install pyyaml
```

### 2. Configure Your Channels

Edit `channels.yaml` to add your channels:

```yaml
channels:
  - name: "My Signal Channel"
    username: "@YourChannelHere"
    enabled: true
    auto_parse: true
    auto_trade: false
    parser_type: "standard"
    risk_per_trade: 1.0
    instruments:
      - XAUUSD
      - GC
```

### 3. Run the Multi-Channel Harvester

```bash
python telegram_harvester_multi.py
```

---

## 📁 File Structure

```
telegram-reader/
├── channels.yaml                    # Channel configuration
├── telegram_harvester_multi.py      # Multi-channel harvester
├── status.html                      # Dashboard (open in browser)
├── history/                         # Per-channel history files
│   ├── Sureshotfx_Signals_Free_history.txt
│   ├── GoldTraderMo_history.txt
│   └── ...
├── orders_out/                      # Order commands for NinjaTrader
├── status_out/                      # Status updates from NinjaTrader
└── TelegramReader.session           # Your auth session
```

---

## ⚙️ Configuration Guide

### Channel Settings

| Setting | Type | Description |
|---------|------|-------------|
| `name` | string | Display name for the channel |
| `username` | string | Telegram username (with @) |
| `enabled` | boolean | Enable/disable monitoring |
| `auto_parse` | boolean | Parse signals automatically |
| `auto_trade` | boolean | Execute trades automatically |
| `parser_type` | string | Which parser to use (standard, goldtrader, custom) |
| `risk_per_trade` | float | % of account to risk per trade |
| `instruments` | list | Instruments this channel trades |

### Global Settings

```yaml
global:
  ninjatrader:
    base_path: "C:\\MCPServer"
    account: "Sim101"
    
  risk:
    max_daily_risk: 5.0          # Max % risk per day
    max_positions: 3             # Max simultaneous positions
    max_per_instrument: 1        # Max per instrument
```

---

## 🎨 Dashboard

Open `status.html` in your browser to see:
- Channel status (active/disabled)
- Messages per channel
- Recent signals
- Overall statistics

---

## 🔧 Adding New Channels

1. Open `channels.yaml`
2. Add a new channel entry:

```yaml
  - name: "New Channel"
    username: "@NewChannel"
    enabled: true
    auto_parse: true
    auto_trade: false
    parser_type: "standard"
    risk_per_trade: 1.0
    instruments:
      - XAUUSD
```

3. Restart the harvester (Ctrl+C, then run again)

---

## 📊 Per-Channel History Files

Each channel gets its own history file in the `history/` folder:

- `Sureshotfx_Signals_Free_history.txt`
- `GoldTraderMo_history.txt`
- etc.

This makes it easy to:
- Track which channel sent which signal
- Analyze performance per channel
- Debug channel-specific issues

---

## 🚀 Comparison: Single vs Multi-Channel

### Old (telegram_harvester.py):
- ❌ One channel only
- ❌ Hardcoded settings
- ❌ Mixed history file

### New (telegram_harvester_multi.py):
- ✅ Unlimited channels
- ✅ YAML configuration
- ✅ Per-channel history
- ✅ Individual settings
- ✅ Easy to add/remove channels

---

## 🔄 Migration from Single to Multi

If you were using the old `telegram_harvester.py`:

1. Your session file works with both versions
2. Your `.env` file works with both versions
3. Just create `channels.yaml` and switch to the new script
4. Your old `history.txt` is still there, won't be overwritten

---

## 📝 Next Steps

### Phase 2 (Coming Soon):
- [ ] Web-based configuration UI
- [ ] Real-time dashboard updates (WebSocket)
- [ ] Signal parsing for multiple formats
- [ ] Trade execution tracking
- [ ] Performance analytics per channel
- [ ] Mobile app

---

## ❓ FAQ

**Q: Can I run both old and new versions?**  
A: Yes! They use different history files and don't conflict.

**Q: How many channels can I monitor?**  
A: Tested with 20+ channels. No practical limit.

**Q: Can each channel have different signal formats?**  
A: Yes! Use `parser_type` to specify different parsers.

**Q: Do I need to re-authenticate?**  
A: No! Your existing session file works.

**Q: Can I enable/disable channels without restarting?**  
A: Currently requires restart. Hot-reload coming in Phase 2.

---

## 🐛 Troubleshooting

### "PyYAML not installed"
```bash
pip install pyyaml
```

### "Config file not found"
Make sure `channels.yaml` is in the `telegram-reader` folder.

### Channel not monitoring
- Check `enabled: true` in `channels.yaml`
- Verify username is correct (include @)
- Check logs for connection errors

---

**Ready to monitor 10+ channels?** Edit `channels.yaml` and run it! 🚀
