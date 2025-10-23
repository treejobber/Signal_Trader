# 🚀 Signal Trader Pro Dashboard - Setup Guide

## Professional Web Dashboard with Real-Time Updates

---

## ✨ Features

✅ **Interactive Web UI** - Add/edit channels from your browser  
✅ **Real-Time Updates** - WebSocket connection for live data  
✅ **Mobile Responsive** - Works on phone, tablet, desktop  
✅ **REST API** - Programmatic access to all features  
✅ **Multi-Channel Support** - Monitor 10+ channels simultaneously  
✅ **Per-Channel Analytics** - Track performance individually  
✅ **Beautiful Design** - Modern, professional interface  

---

## 📋 Installation

### Step 1: Pull Latest Code from GitHub

```bash
cd C:\Users\scott\Desktop\Signal_Trader
git pull
```

### Step 2: Install Dashboard Dependencies

```bash
cd telegram-reader
pip install -r requirements_dashboard.txt
```

This installs:
- Flask (web server)
- Flask-SocketIO (real-time updates)
- Flask-CORS (API access)
- PyYAML (configuration)

### Step 3: Verify Files

Make sure you have:
```
telegram-reader/
├── dashboard_server.py          ✅ Backend server
├── dashboard.html               ✅ Frontend UI
├── channels.yaml                ✅ Configuration
├── telegram_harvester_multi.py  ✅ Multi-channel harvester
└── requirements_dashboard.txt   ✅ Dependencies
```

---

## 🎯 Usage

### Running the System

You'll run **TWO** programs:

#### Terminal 1: Start the Dashboard Server

```bash
cd C:\Users\scott\Desktop\Signal_Trader\telegram-reader
python dashboard_server.py
```

You'll see:
```
Starting Signal Trader Dashboard Server
Dashboard will be available at: http://localhost:5000
```

#### Terminal 2: Start the Telegram Harvester

```bash
cd C:\Users\scott\Desktop\Signal_Trader\telegram-reader
python telegram_harvester_multi.py
```

This monitors your Telegram channels and feeds data to the dashboard.

#### Open Dashboard in Browser

Go to: **http://localhost:5000**

---

## 🎨 Dashboard Features

### 1. **Overview Statistics**
- Total channels configured
- Active channels monitoring
- Messages received today
- System uptime

### 2. **Channel Management**
Click **"+ Add Channel"** to add a new channel:
- Channel name
- Telegram username
- Enable/disable monitoring
- Parser type selection
- Risk settings
- Instruments traded

### 3. **Live Channel Cards**
Each channel shows:
- Status (Active/Disabled)
- Messages today
- Last message time
- Parser type
- Instruments monitored

### 4. **Recent Signals**
Real-time feed of:
- Timestamp
- Channel name
- Signal message

### 5. **Real-Time Updates**
Dashboard updates every 5 seconds automatically via WebSocket!

---

## 🔧 Configuration

### Adding Channels via Web UI

1. Click **"+ Add Channel"** button
2. Fill in the form:
   - **Name:** Display name (e.g., "Gold Signals VIP")
   - **Username:** Telegram @username
   - **Enabled:** Turn on to monitor
   - **Parser Type:** standard, goldtrader, or custom
   - **Risk %:** How much to risk per trade
   - **Instruments:** Comma-separated (XAUUSD, GC, ES)
3. Click **"Add Channel"**
4. **Restart** telegram_harvester_multi.py to activate

### Adding Channels via YAML (Alternative)

Edit `channels.yaml`:

```yaml
channels:
  - name: "My New Channel"
    username: "@NewChannel"
    enabled: true
    auto_parse: true
    auto_trade: false
    parser_type: "standard"
    risk_per_trade: 1.0
    instruments:
      - XAUUSD
      - GC
```

---

## 📊 API Endpoints

The dashboard provides a REST API:

### Get All Channels
```bash
curl http://localhost:5000/api/channels
```

### Get Statistics
```bash
curl http://localhost:5000/api/stats
```

### Get Recent Signals
```bash
curl http://localhost:5000/api/signals/recent?limit=50
```

### Add Channel
```bash
curl -X POST http://localhost:5000/api/channels \
  -H "Content-Type: application/json" \
  -d '{"name":"Test","username":"@TestChannel","enabled":true}'
```

### Update Channel
```bash
curl -X PUT http://localhost:5000/api/channels/@ChannelName \
  -H "Content-Type: application/json" \
  -d '{"enabled":false}'
```

### Delete Channel
```bash
curl -X DELETE http://localhost:5000/api/channels/@ChannelName
```

---

## 🌐 Accessing from Phone/Tablet

### On Same Network

1. Find your computer's IP address:
   ```bash
   ipconfig
   ```
   Look for "IPv4 Address" (e.g., 192.168.1.100)

2. On your phone/tablet, open browser:
   ```
   http://192.168.1.100:5000
   ```

### Over Internet (Advanced)

Use ngrok or similar tunneling service:
```bash
ngrok http 5000
```

---

## 🔄 Workflow

### Normal Operation

1. **Start Dashboard Server** (Terminal 1)
   - Runs web interface
   - Provides API
   - Serves real-time updates

2. **Start Telegram Harvester** (Terminal 2)
   - Monitors channels
   - Writes to history files
   - Creates order files

3. **Configure via Browser**
   - Add/remove channels
   - Change settings
   - View live data

4. **NinjaTrader** (Optional - when ready)
   - Reads order files
   - Executes trades
   - Writes status updates

---

## 🐛 Troubleshooting

### "Port 5000 already in use"

Another program is using port 5000. Either:

**Option A:** Stop the other program

**Option B:** Change port in dashboard_server.py:
```python
# Line 508
socketio.run(app, host='0.0.0.0', port=5001, debug=False)
```

Then access at: http://localhost:5001

### "Cannot connect to server"

- Make sure dashboard_server.py is running
- Check firewall isn't blocking port 5000
- Try http://127.0.0.1:5000 instead

### Dashboard not updating

- Check telegram_harvester_multi.py is running
- Verify channels.yaml has enabled channels
- Look at terminal logs for errors

### Changes not appearing

- Restart telegram_harvester_multi.py after editing channels
- Refresh browser (F5 or Ctrl+R)
- Clear browser cache if needed

---

## 📱 Mobile Screenshots

The dashboard is fully responsive:
- 📱 **Phone:** Single column layout
- 📱 **Tablet:** Two column layout
- 💻 **Desktop:** Full width layout

---

## ⚡ Performance

- **Dashboard Server:** Uses ~50MB RAM
- **Telegram Harvester:** Uses ~100MB RAM per 10 channels
- **Updates:** Every 5 seconds (configurable)
- **WebSocket:** Low latency real-time updates

---

## 🔐 Security Notes

For production use, add:
- Authentication (username/password)
- HTTPS/SSL certificates
- API rate limiting
- CORS restrictions

Currently configured for **local development** (no authentication).

---

## 🎯 Next Steps

Once dashboard is running:

1. ✅ Add all your channels via web UI
2. ✅ Monitor them in real-time
3. ✅ Add signal parsing (next phase)
4. ✅ Connect NinjaTrader
5. ✅ Enable auto-trading

---

## 💡 Pro Tips

1. **Keep both terminals running** - Dashboard server + Harvester
2. **Bookmark http://localhost:5000** - Quick access
3. **Use mobile browser** - Monitor on the go
4. **Check logs regularly** - Look for errors
5. **Test on Sim account first** - Before live trading

---

## 📞 Quick Reference

| Component | Command | Port |
|-----------|---------|------|
| Dashboard Server | `python dashboard_server.py` | 5000 |
| Telegram Harvester | `python telegram_harvester_multi.py` | N/A |
| Web Dashboard | Open browser | http://localhost:5000 |
| API Base | Use in scripts | http://localhost:5000/api |

---

**Ready to launch?** Run the servers and open http://localhost:5000! 🚀
