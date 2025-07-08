# 🤖 BUNDELING - Telegram Bot Ecosystem

> **Dual-Bot System untuk Data Input & Analisis Togel**  
> Sistem bot Telegram yang terintegrasi dengan Google Sheets untuk pencatatan data dan analisis prediksi.

---

## 🚀 Quick Start Commands

### 🎯 Core Commands
- **🌟 Run All Bots**: `python main.py` - Menjalankan kedua bot secara bersamaan
- **📝 Run Input Bot**: `cd bot1 && python bot1.py` - Bot untuk input data ke Google Sheets
- **📊 Run Analysis Bot**: `cd bot2 && python bot2.py` - Bot untuk analisis dan prediksi
- **🔧 Install Dependencies**: `pip install -r bot1/requirements.txt`

### 🧪 Testing & Debugging
- **✅ Test Dependencies**: `python -c "import telegram; import gspread; print('Dependencies OK')"`
- **🔍 Test Google Sheets**: `python -c "import gspread; print('Google Sheets OK')"`
- **🤖 Test Telegram Bot**: `python -c "from telegram.ext import Application; print('Telegram Bot OK')"`

---

## 🏗️ Architecture Overview

### 🎮 Main Controller
- **📁 `main.py`**: Multi-threaded bot runner yang menjalankan kedua bot secara concurrent
- **🔄 Threading**: Menggunakan Python threading untuk menjalankan bot1 dan bot2 secara parallel
- **⚡ Auto-restart**: Error handling dengan graceful shutdown pada KeyboardInterrupt

### 🤖 Bot 1 - Data Input Bot (`bot1/`)
- **🎯 Purpose**: Telegram bot untuk input data ke Google Sheets
- **💬 Features**: 
  - Conversation handler untuk guided input
  - Direct input format: `tanggal, periode, result`
  - Data validation (tanggal DD/MM/YYYY, 4-digit periode & result)
  - User tracking dan timestamp otomatis
- **📋 Commands**: `/start`, `/input`, `/showdata`, `/help`, `/cancel`

### 📊 Bot 2 - Analysis Bot (`bot2/`)
- **🎯 Purpose**: Bot analisis dan prediksi berdasarkan data Google Sheets
- **🧠 Features**:
  - 7 metode analisis berbeda (frekuensi, hot/cold numbers, dll)
  - Prediksi berdasarkan pola tanggal dan periode
  - Analisis statistik menggunakan pandas & numpy
  - Weighted random generation dan cross pattern
- **📋 Commands**: `/start`, `/analisis`, `/prediksi`, `/metode`, `/help`

### 🔗 Data Flow
```
Telegram User → Bot1 (Input) → Google Sheets → Bot2 (Analysis) → Telegram User
```

---

## 📦 Dependencies & Environment

### 🔧 Core Libraries
- **🤖 `python-telegram-bot`**: Telegram Bot API wrapper
- **📊 `gspread`**: Google Sheets API integration
- **🔐 `google-auth`**: Google service account authentication
- **🌍 `python-dotenv`**: Environment variable management
- **📈 `pandas`**: Data analysis dan manipulation
- **🔢 `numpy`**: Numerical computing untuk analisis statistik

### 🔑 Authentication & Config
- **🔐 Google Service Account**: `credentials.json` untuk akses Google Sheets
- **⚙️ Environment Variables**: 
  - `TELEGRAM_BOT_TOKEN`: Token bot Telegram
  - `GOOGLE_SPREADSHEET_ID`: ID spreadsheet Google Sheets
  - `GOOGLE_CREDENTIALS_FILE`: Path ke credentials.json
  - `SHEET_NAME`: Nama worksheet (default: Sheet1)

---

## 🎨 Code Style Guidelines

### 📝 Naming Conventions
- **🐍 Variables & Functions**: `snake_case` (contoh: `user_data`, `get_tanggal`)
- **🏛️ Classes**: `PascalCase` (contoh: `DataInputBot`, `TogelAnalysisBot`)
- **📁 Files**: `snake_case.py` (contoh: `bot1.py`, `bot2.py`)

### 📚 Import Organization
```python
# 1. Standard library
import logging
from datetime import datetime

# 2. Third-party libraries
from telegram import Update
import gspread
import pandas as pd

# 3. Local modules
from .config import settings
```

### 🛡️ Error Handling
- **🔍 Try-catch blocks**: Untuk semua operasi eksternal (Google Sheets, Telegram API)
- **📝 Logging**: Menggunakan built-in logging module dengan level INFO
- **⚠️ User feedback**: Error messages yang user-friendly dalam bahasa Indonesia

### 🔄 Async Programming
- **⚡ Async handlers**: Semua Telegram handlers menggunakan `async/await`
- **🎯 Context typing**: Menggunakan `ContextTypes.DEFAULT_TYPE` untuk type safety
- **🔗 Conversation handling**: ConversationHandler untuk multi-step interactions

### 🌐 Internationalization
- **🇮🇩 Indonesian**: Semua user-facing messages dalam bahasa Indonesia
- **📖 Comments**: Code comments dalam bahasa Indonesia untuk konteks lokal
- **📚 Docstrings**: Public methods menggunakan docstrings yang jelas
