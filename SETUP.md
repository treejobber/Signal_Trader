# Setup Guide for Signal_Trader

## 📋 Complete Setup Checklist

Follow these steps in order to get Signal_Trader running.

### ✅ Step 1: Get Telegram API Credentials

1. Go to https://my.telegram.org/apps
2. Log in with your phone number
3. Click "API Development Tools"
4. Fill in the form:
   - App title: `Signal_Trader`
   - Short name: `signaltrader`
   - Platform: Other
5. Click "Create application"
6. **Copy your API_ID and API_HASH** - you'll need these!

### ✅ Step 2: Set Up Environment Variables

1. Copy the template:
   ```bash
   cp .env.template .env
   ```

2. Edit `.env` file with your credentials:
   ```bash
   API_ID=your_api_id_here      # Paste the number you got
   API_HASH=your_api_hash_here  # Paste the hash you got
   CHANNEL=@Sureshotfx_Signals_Free  # Or your channel
   ```

### ✅ Step 3: Install Python Dependencies

```bash
# Create virtual environment
python -m venv venv

# Activate it
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

# Install required packages
pip install -r requirements.txt
```

### ✅ Step 4: First Run (Authentication)

```bash
cd telegram-reader
python telegram_harvester.py
```

**You'll be asked to:**
1. Enter your phone number (with country code, e.g., +1234567890)
2. Enter the code sent to your Telegram app
3. If you have 2FA, enter your password

**This creates a `.session` file** - keep it safe!

### ✅ Step 5: Configure NinjaTrader

1. Open NinjaTrader 8
2. Go to Tools → Import NinjaScript
3. Select `ninjatrader-strategy/FileOrderBridge.cs`
4. Right-click the chart → Strategies → Add Strategy
5. Select "FileOrderBridge"
6. Configure paths:
   - Set `MCP Server Base Path` to your project folder
   - Example: `C:\Users\YourName\Signal_Trader`
7. Enable the strategy

### ✅ Step 6: Test the System

1. **Check logs:**
   ```bash
   # In telegram-reader folder
   tail -f telegram_harvester.log
   ```

2. **Send a test command:**
   The script will monitor your Telegram channel and create order files in `orders_out/`

3. **Verify NinjaTrader receives it:**
   Check NinjaTrader's output window for messages

### ✅ Step 7: Monitor and Maintain

1. **Keep the script running:**
   - Use Windows Task Scheduler, or
   - Run in a terminal you keep open, or
   - Use `nohup` on Linux/Mac

2. **Check logs regularly:**
   ```bash
   telegram_harvester.log
   ```

3. **Backup your session file:**
   The `.session` file prevents re-authentication

## 🔧 Troubleshooting

### "API_ID not set" Error
- Make sure `.env` file exists (not `.env.template`)
- Check that API_ID is a number (no quotes)
- Verify API_HASH is set

### Phone Verification Issues
- Use international format: +1234567890
- Check you have access to your Telegram account
- Try "Call me" option if code doesn't arrive

### "File Not Found" Errors
- Make sure directories exist:
  ```bash
  mkdir -p telegram-reader/orders_out
  mkdir -p telegram-reader/status_out
  ```

### NinjaTrader Not Receiving Orders
- Check paths in FileOrderBridge strategy
- Verify `orders_out` folder location
- Look at NT output window for errors
- Ensure strategy is enabled

## 📚 Next Steps

Once setup is complete:

1. Read [QUICK_REFERENCE.md](docs/QUICK_REFERENCE.md) for daily operations
2. Review [ERROR_HANDLING_IMPROVEMENTS.md](docs/ERROR_HANDLING_IMPROVEMENTS.md)
3. Check [GIT_WORKFLOW_GUIDE.md](docs/GIT_WORKFLOW_GUIDE.md) if you want to make changes

## 🆘 Still Having Issues?

1. Check all documentation in `docs/` folder
2. Review error messages in `telegram_harvester.log`
3. Verify all paths are correct
4. Test on paper/sim account first!

## ⚠️ Important Reminders

- ✅ Never commit `.env` file to Git
- ✅ Keep your `.session` file secure
- ✅ Test on Sim account before live trading
- ✅ Monitor logs regularly
- ✅ Keep backups of your configuration

---

**Setup complete?** Start the harvester and watch the logs! 🚀
