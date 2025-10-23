# Signal_Trader

**Automated trading system that monitors Telegram channels for trading signals and executes them via NinjaTrader.**

## 🎯 Features

- ✅ **Telegram Integration**: Monitors trading signal channels in real-time
- ✅ **Error Handling**: Robust error handling for all file operations
- ✅ **Logging**: Comprehensive logging with rotation
- ✅ **NinjaTrader Bridge**: Seamless integration with NinjaTrader 8
- ✅ **MCP Server**: Model Context Protocol server for command processing
- ✅ **Documentation**: Complete setup and usage guides

## 📁 Project Structure

```
Signal_Trader/
├── telegram-reader/          # Telegram monitoring scripts
│   └── telegram_harvester.py # Main script with error handling
├── mpc-server/               # MCP server for command processing
│   ├── plugins/             # Server plugins
│   └── config/              # Server configuration
├── ninjatrader-strategy/     # NinjaTrader integration
│   └── FileOrderBridge.cs   # C# strategy for NT8
├── docs/                     # Documentation
│   ├── README.md            # Main documentation
│   ├── QUICK_REFERENCE.md   # Quick setup guide
│   ├── GIT_WORKFLOW_GUIDE.md
│   └── ERROR_HANDLING_IMPROVEMENTS.md
├── .env.template            # Environment variables template
├── .gitignore              # Git ignore file
└── README.md               # This file
```

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- NinjaTrader 8
- Telegram API credentials ([Get them here](https://my.telegram.org/apps))
- Git

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/treejobber/Signal_Trader.git
   cd Signal_Trader
   ```

2. **Set up Python environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install telethon python-dotenv
   ```

3. **Configure environment variables:**
   ```bash
   cp .env.template .env
   # Edit .env with your credentials
   ```

4. **Create required directories:**
   ```bash
   mkdir -p telegram-reader/orders_out
   mkdir -p telegram-reader/status_out
   ```

### Running the System

1. **Start the Telegram Harvester:**
   ```bash
   cd telegram-reader
   python telegram_harvester.py
   ```

2. **Configure NinjaTrader:**
   - Import `FileOrderBridge.cs` strategy
   - Set paths in strategy properties
   - Enable strategy on chart

3. **Start MCP Server (optional):**
   ```bash
   cd mpc-server
   python main.py
   ```

## 📖 Documentation

- **[Quick Reference](docs/QUICK_REFERENCE.md)** - Fast setup guide
- **[Complete Guide](docs/README.md)** - Detailed documentation
- **[Git Workflow](docs/GIT_WORKFLOW_GUIDE.md)** - How to contribute
- **[Error Handling](docs/ERROR_HANDLING_IMPROVEMENTS.md)** - Improvements made

## 🔒 Security

- **Never commit `.env` file** - It contains sensitive credentials
- **Rotate API keys regularly** - Especially if exposed
- **Use paper trading first** - Test on Sim account before live
- **Keep backups** - Of your configuration and session files

## ⚙️ Configuration

### Telegram Settings (in `.env`):

```bash
API_ID=your_telegram_api_id
API_HASH=your_telegram_api_hash
CHANNEL=@YourTradingChannel
```

### NinjaTrader Settings:

Configure paths in the FileOrderBridge strategy:
- `OrdersFolder`: Where to read commands
- `StatusFolder`: Where to write status updates

## 🐛 Troubleshooting

### "API_ID not set" error:
- Make sure you've created `.env` file from `.env.template`
- Check that API_ID and API_HASH are set correctly

### Session file errors:
- Delete `*.session` files and restart to re-authenticate

### File permission errors:
- Ensure directories exist and are writable
- Check that paths are correct in configuration

## 📊 System Architecture

```
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│  Telegram    │─────▶│  Python      │─────▶│  NinjaTrader │
│  Channel     │      │  Harvester   │      │  Bridge      │
└──────────────┘      └──────────────┘      └──────────────┘
                            │                       │
                            ▼                       ▼
                     ┌──────────────┐      ┌──────────────┐
                     │  SQLite DB   │      │  Live Market │
                     │  (optional)  │      │              │
                     └──────────────┘      └──────────────┘
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

See [GIT_WORKFLOW_GUIDE.md](docs/GIT_WORKFLOW_GUIDE.md) for details.

## 📝 License

This project is for educational and personal use. Trade at your own risk.

## ⚠️ Disclaimer

Trading involves substantial risk. This software is provided as-is with no guarantees. Always test on paper accounts first. Past performance does not guarantee future results.

## 📞 Support

For issues or questions:
- Check the [documentation](docs/)
- Review the [troubleshooting section](#🐛-troubleshooting)
- Open an issue on GitHub

---

**Version:** 2.0  
**Last Updated:** October 22, 2025  
**Status:** Active Development
