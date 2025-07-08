import logging
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler
)
import gspread
from google.oauth2.service_account import Credentials
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# States for conversation
TANGGAL, PERIODE, RESULT = range(3)

class DataInputBot:
    def __init__(self):
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.spreadsheet_id = os.getenv('GOOGLE_SPREADSHEET_ID')
        self.credentials_file = os.getenv('GOOGLE_CREDENTIALS_FILE')
        self.sheet_name = os.getenv('SHEET_NAME', 'Sheet1')  # Default to Sheet1 if not specified
        
        # Initialize Google Sheets
        self.setup_google_sheets()
        
    def setup_google_sheets(self):
        """Setup Google Sheets connection"""
        try:
            scope = [
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive'
            ]
            
            creds = Credentials.from_service_account_file(
                self.credentials_file, 
                scopes=scope
            )
            
            self.gc = gspread.authorize(creds)
            self.sheet = self.gc.open_by_key(self.spreadsheet_id).worksheet(self.sheet_name)
            
            # Setup header if not exists
            try:
                headers = self.sheet.row_values(1)
                if not headers or headers != ['Timestamp', 'Tanggal', 'Periode', 'Result', 'User']:
                    self.sheet.clear()
                    self.sheet.append_row(['Timestamp', 'Tanggal', 'Periode', 'Result', 'User'])
            except Exception as e:
                logger.warning(f"Header check failed, creating new: {e}")
                self.sheet.append_row(['Timestamp', 'Tanggal', 'Periode', 'Result', 'User'])
                
        except Exception as e:
            logger.error(f"Error setting up Google Sheets: {e}")
            raise
            
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start command handler"""
        user = update.effective_user
        await update.message.reply_text(
            f"Halo {user.first_name}! 👋\n\n"
            "Selamat datang di Bot Input Data Telegram!\n"
            "Bot ini akan membantu Anda menginput data ke spreadsheet.\n\n"
            "Gunakan /input untuk mulai input data baru.\n"
            "Gunakan /showdata untuk melihat data yang sudah diinput.\n"
            "Gunakan /help untuk melihat perintah yang tersedia."
        )
        
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Help command handler"""
        help_text = """
📋 *Perintah yang tersedia:*

/start - Memulai bot
/input - Memulai input data baru
/showdata - Menampilkan semua data yang sudah diinput
/cancel - Membatalkan proses input data
/help - Menampilkan bantuan ini

📝 *Format Input Data:*
1. Tanggal (format: DD/MM/YYYY)
2. Periode (contoh: 1111)
3. Result (contoh: 1234)

*Cara Input:*
- Bertahap: ketik /input lalu ikuti petunjuk
- Langsung: kirim "01/12/2025, 1111, 1234"
"""
        await update.message.reply_text(help_text, parse_mode='Markdown')
        
    async def start_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start data input process"""
        await update.message.reply_text(
            "📋 *Memulai Input Data Baru*\n\n"
            "Silakan masukkan *tanggal* (format: DD/MM/YYYY)\n"
            "Contoh: 01/12/2025\n\n"
            "Ketik /cancel untuk membatalkan.",
            parse_mode='Markdown'
        )
        return TANGGAL
        
    async def get_tanggal(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get date input"""
        tanggal_text = update.message.text.strip()
        
        # Validate date format
        try:
            datetime.strptime(tanggal_text, '%d/%m/%Y')
            context.user_data['tanggal'] = tanggal_text
            
            await update.message.reply_text(
                f"✅ Tanggal: {tanggal_text}\n\n"
                "Sekarang masukkan *periode*.\n"
                "Contoh: 1111",
                parse_mode='Markdown'
            )
            return PERIODE
            
        except ValueError:
            await update.message.reply_text(
                "❌ Format tanggal tidak valid!\n"
                "Silakan masukkan tanggal dengan format DD/MM/YYYY\n"
                "Contoh: 01/12/2025"
            )
            return TANGGAL
            
    async def get_periode(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get period input"""
        periode = update.message.text.strip()
        
        # Simple validation for period (4 digits)
        if not periode.isdigit() or len(periode) != 4:
            await update.message.reply_text(
                "❌ Periode harus berupa 4 digit angka!\n"
                "Contoh: 1111"
            )
            return PERIODE
            
        context.user_data['periode'] = periode
        
        await update.message.reply_text(
            f"✅ Periode: {periode}\n\n"
            "Sekarang masukkan *result*.\n"
            "Contoh: 1234",
            parse_mode='Markdown'
        )
        return RESULT
        
    async def get_result(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get result input and save to spreadsheet"""
        result = update.message.text.strip()
        
        # Simple validation for result (4 digits)
        if not result.isdigit() or len(result) != 4:
            await update.message.reply_text(
                "❌ Result harus berupa 4 digit angka!\n"
                "Contoh: 1234"
            )
            return RESULT
            
        context.user_data['result'] = result
        
        # Get user info
        user = update.effective_user
        username = user.username if user.username else f"{user.first_name} {user.last_name or ''}".strip()
        
        # Save to spreadsheet
        try:
            timestamp = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
            row_data = [
                timestamp,
                context.user_data['tanggal'],
                context.user_data['periode'],
                result,
                username
            ]
            
            self.sheet.append_row(row_data)
            
            # Send confirmation with the saved data
            confirmation_text = f"""
✅ *Data berhasil disimpan!*

📅 *Tanggal:* {context.user_data['tanggal']}
🔢 *Periode:* {context.user_data['periode']}
📊 *Result:* {result}
👤 *User:* {username}
⏱ *Timestamp:* {timestamp}

Gunakan /input untuk menambah data baru.
"""
            
            await update.message.reply_text(confirmation_text, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error saving to spreadsheet: {e}")
            await update.message.reply_text(
                "❌ Terjadi kesalahan saat menyimpan data!\n"
                "Silakan coba lagi nanti atau hubungi administrator."
            )
        
        # Clear user data
        context.user_data.clear()
        return ConversationHandler.END
        
    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Cancel the conversation"""
        context.user_data.clear()
        await update.message.reply_text(
            "❌ Proses input data dibatalkan.\n"
            "Gunakan /input untuk memulai lagi."
        )
        return ConversationHandler.END
        
    async def show_data(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show all data that has been input"""
        try:
            # Get all records from the sheet
            records = self.sheet.get_all_records()
            
            if not records:
                await update.message.reply_text("📭 Tidak ada data yang tersimpan.")
                return
                
            # Get current user
            user = update.effective_user
            username = user.username if user.username else f"{user.first_name} {user.last_name or ''}".strip()
            
            # Filter data by user (optional, remove if you want to show all data)
            user_records = [r for r in records if r['User'] == username]
            
            if not user_records:
                await update.message.reply_text("📭 Anda belum menginput data apapun.")
                return
                
            # Format the data for display
            message = "📋 *Data yang sudah Anda input:*\n\n"
            for idx, record in enumerate(user_records, 1):
                message += (
                    f"*{idx}. {record['Tanggal']}*\n"
                    f"   Periode: {record['Periode']}\n"
                    f"   Result: {record['Result']}\n"
                    f"   Waktu: {record['Timestamp']}\n\n"
                )
                
            # Split long messages to avoid Telegram message length limit
            if len(message) > 4000:
                parts = [message[i:i+4000] for i in range(0, len(message), 4000)]
                for part in parts:
                    await update.message.reply_text(part, parse_mode='Markdown')
            else:
                await update.message.reply_text(message, parse_mode='Markdown')
                
        except Exception as e:
            logger.error(f"Error showing data: {e}")
            await update.message.reply_text(
                "❌ Terjadi kesalahan saat mengambil data.\n"
                "Silakan coba lagi nanti atau hubungi administrator."
            )
        
    def run(self):
        """Run the bot"""
        # Create application
        application = Application.builder().token(self.bot_token).build()
        
        # Add conversation handler for data input
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler('input', self.start_input)],
            states={
                TANGGAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.get_tanggal)],
                PERIODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.get_periode)],
                RESULT: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.get_result)],
            },
            fallbacks=[CommandHandler('cancel', self.cancel)],
        )
        
        # Add handlers
        application.add_handler(CommandHandler('start', self.start))
        application.add_handler(CommandHandler('help', self.help_command))
        application.add_handler(CommandHandler('showdata', self.show_data))
        application.add_handler(conv_handler)
        
        # Add handler for direct input (format: tanggal, periode, result)
        application.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            self.handle_direct_input
        ))
        
        # Run the bot
        logger.info("🤖 Bot Telegram Data Input sedang berjalan...")
        application.run_polling(allowed_updates=Update.ALL_TYPES)
        
    async def handle_direct_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle direct input in format: tanggal, periode, result"""
        text = update.message.text.strip()
        
        # Check if the input matches the expected format
        parts = [part.strip() for part in text.split(',')]
        if len(parts) != 3:
            return  # Not our format, ignore
            
        tanggal, periode, result = parts
        
        # Validate date
        try:
            datetime.strptime(tanggal, '%d/%m/%Y')
        except ValueError:
            await update.message.reply_text(
                "❌ Format tanggal salah. Gunakan DD/MM/YYYY\n"
                "Contoh: 01/12/2025, 1111, 1234"
            )
            return
            
        # Validate periode and result (4 digits each)
        if not (periode.isdigit() and len(periode) == 4 and 
                result.isdigit() and len(result) == 4):
            await update.message.reply_text(
                "❌ Periode dan Result harus 4 digit angka\n"
                "Contoh: 01/12/2025, 1111, 1234"
            )
            return
            
        # Get user info
        user = update.effective_user
        username = user.username if user.username else f"{user.first_name} {user.last_name or ''}".strip()
        
        # Save to spreadsheet
        try:
            timestamp = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
            row_data = [timestamp, tanggal, periode, result, username]
            self.sheet.append_row(row_data)
            
            # Send confirmation
            confirmation_text = f"""
✅ *Data berhasil disimpan!*

📅 *Tanggal:* {tanggal}
🔢 *Periode:* {periode}
📊 *Result:* {result}
👤 *User:* {username}
⏱ *Timestamp:* {timestamp}

Gunakan /input untuk menambah data baru.
"""
            await update.message.reply_text(confirmation_text, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error saving direct input: {e}")
            await update.message.reply_text(
                "❌ Terjadi kesalahan saat menyimpan data!\n"
                "Silakan coba lagi nanti atau hubungi administrator."
            )

if __name__ == '__main__':
    try:
        bot = DataInputBot()
        bot.run()
    except Exception as e:
        logger.error(f"Bot failed to start: {e}")
        