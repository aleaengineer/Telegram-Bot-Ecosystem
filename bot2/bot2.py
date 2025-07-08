import logging
from datetime import datetime
import numpy as np
import pandas as pd
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import gspread
from google.oauth2.service_account import Credentials
import os
from dotenv import load_dotenv
from collections import Counter
import random

# Load environment variables
load_dotenv()

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class TogelAnalysisBot:
    def __init__(self):
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.spreadsheet_id = os.getenv('GOOGLE_SPREADSHEET_ID')
        self.credentials_file = os.getenv('GOOGLE_CREDENTIALS_FILE')
        self.sheet_name = os.getenv('SHEET_NAME', 'Sheet1')
        
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
            
        except Exception as e:
            logger.error(f"Error setting up Google Sheets: {e}")
            raise
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start command handler"""
        user = update.effective_user
        await update.message.reply_text(
            f"Halo {user.first_name}! 👋\n\n"
            "Selamat datang di *Bot Analisis Togel*\n\n"
            "📊 Saya akan menganalisis data dari spreadsheet untuk membantu memprediksi angka togel.\n\n"
            "🔍 *Perintah yang tersedia:*\n"
            "/start - Memulai bot\n"
            "/help - Menampilkan bantuan\n"
            "/analisis - Melakukan analisis data terbaru\n"
            "/prediksi - Menampilkan prediksi angka\n"
            "/metode - Menjelaskan metode analisis yang digunakan",
            parse_mode='Markdown'
        )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Help command handler"""
        help_text = """
🔍 *BOT ANALISIS TOGEL* 🔍

📊 *Perintah yang tersedia:*
/start - Memulai bot
/help - Menampilkan bantuan ini
/analisis - Analisis data terbaru dari spreadsheet
/prediksi - Menampilkan prediksi angka untuk periode berikutnya
/metode - Menjelaskan metode analisis yang digunakan

📈 *Metode Analisis:*
1. Analisis Frekuensi Angka
2. Pola Angka Panas/Dingin
3. Prediksi Berdasarkan Tanggal
4. Pola Berdasarkan Periode
5. Angka Acak Terbobot
6. Analisis Angka Kembar
7. Pola Urutan Angka
"""
        await update.message.reply_text(help_text, parse_mode='Markdown')
    
    async def metode_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Explain analysis methods"""
        methods_text = """
📚 *Metode Analisis Togel yang Digunakan:*

1. *Analisis Frekuensi Angka*:
   - Mencari angka yang paling sering muncul (hot numbers)
   - Mencari angka yang jarang muncul (cold numbers)

2. *Pola Angka Panas/Dingin*:
   - Angka panas: angka yang muncul dalam 5 periode terakhir
   - Angka dingin: angka yang tidak muncul dalam 10 periode terakhir

3. *Prediksi Berdasarkan Tanggal*:
   - Menganalisis pola angka berdasarkan hari/tanggal tertentu

4. *Pola Berdasarkan Periode*:
   - Mencari pola perubahan angka antar periode

5. *Angka Acak Terbobot*:
   - Menghasilkan angka acak dengan bobot berdasarkan frekuensi kemunculan

6. *Analisis Angka Kembar*:
   - Mencari pola angka kembar (double/triple numbers)

7. *Pola Urutan Angka*:
   - Menganalisis urutan angka dari periode ke periode
"""
        await update.message.reply_text(methods_text, parse_mode='Markdown')
    
    def get_dataframe(self):
        """Get data from spreadsheet and return as DataFrame"""
        try:
            records = self.sheet.get_all_records()
            if not records:
                return None
                
            df = pd.DataFrame(records)
            
            # Convert date strings to datetime objects
            df['Tanggal'] = pd.to_datetime(df['Tanggal'], format='%d/%m/%Y', errors='coerce')
            df['Timestamp'] = pd.to_datetime(df['Timestamp'], format='%d/%m/%Y %H:%M:%S', errors='coerce')
            
            # Drop rows with invalid dates
            df = df.dropna(subset=['Tanggal', 'Timestamp'])
            
            # Sort by date descending
            df = df.sort_values('Tanggal', ascending=False)
            
            # Ensure Result is treated as string
            df['Result'] = df['Result'].astype(str)
            
            return df
        
        except Exception as e:
            logger.error(f"Error getting data from spreadsheet: {e}")
            return None
    
    async def analisis_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Analyze the data"""
        try:
            df = self.get_dataframe()
            if df is None or df.empty:
                await update.message.reply_text("❌ Tidak ada data yang ditemukan di spreadsheet.")
                return
            
            # Get last 30 records for analysis
            recent_data = df.head(30)
            
            # Frequency analysis - perbaikan di sini
            all_numbers = []
            for result in recent_data['Result']:
                # Pastikan result adalah string dan tidak kosong
                if isinstance(result, str) and result.strip():
                    all_numbers.extend(list(result.strip()))
            
            if not all_numbers:
                await update.message.reply_text("❌ Tidak ada data angka yang valid untuk dianalisis.")
                return
            
            number_counts = Counter(all_numbers)
            most_common = number_counts.most_common(5)
            least_common = number_counts.most_common()[:-6:-1]
            
            # Hot numbers (appeared in last 5 periods)
            hot_numbers = set()
            for result in recent_data.head(5)['Result']:
                if isinstance(result, str) and result.strip():
                    hot_numbers.update(list(result.strip()))
            
            # Cold numbers (not appeared in last 10 periods)
            cold_numbers = set()
            recent_numbers = set()
            for result in recent_data.head(10)['Result']:
                if isinstance(result, str) and result.strip():
                    recent_numbers.update(list(result.strip()))
            
            all_unique_numbers = set('0123456789')
            cold_numbers = all_unique_numbers - recent_numbers
            
            # Prepare analysis result
            analysis_text = f"""
📊 *Analisis Data Terbaru* (30 periode terakhir)

🔢 *Frekuensi Angka:*
- Angka paling sering muncul: {', '.join([f'{num[0]} ({num[1]}x)' for num in most_common])}
- Angka paling jarang muncul: {', '.join([f'{num[0]} ({num[1]}x)' for num in least_common])}

🔥 *Angka Panas* (muncul dalam 5 periode terakhir):
{', '.join(sorted(hot_numbers)) if hot_numbers else 'Tidak ada data'}

❄️ *Angka Dingin* (tidak muncul dalam 10 periode terakhir):
{', '.join(sorted(cold_numbers)) if cold_numbers else 'Tidak ada'}

📅 *Update terakhir:* {recent_data.iloc[0]['Tanggal'].strftime('%d/%m/%Y')}
"""
            await update.message.reply_text(analysis_text, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in analysis: {e}")
            await update.message.reply_text("❌ Terjadi kesalahan saat menganalisis data.")
    
    async def prediksi_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Generate prediction"""
        try:
            df = self.get_dataframe()
            if df is None or df.empty:
                await update.message.reply_text("❌ Tidak ada data yang ditemukan di spreadsheet.")
                return
            
            # Get recent data
            recent_data = df.head(50)
            
            # Method 1: Most frequent numbers
            all_numbers = []
            for result in recent_data['Result']:
                if isinstance(result, str) and result.strip():
                    all_numbers.extend(list(result.strip()))
            
            if not all_numbers:
                await update.message.reply_text("❌ Tidak ada data angka yang valid untuk diprediksi.")
                return
            
            number_counts = Counter(all_numbers)
            top_numbers = [num[0] for num in number_counts.most_common(10)]
            
            # Method 2: Hot numbers (last 5 periods)
            hot_numbers = set()
            for result in recent_data.head(5)['Result']:
                if isinstance(result, str) and result.strip():
                    hot_numbers.update(list(result.strip()))
            
            # Method 3: Date-based prediction
            last_date = recent_data.iloc[0]['Tanggal']
            day_number = last_date.day % 10
            month_number = last_date.month % 10
            date_based = {str(day_number), str(month_number)}
            
            # Method 4: Weighted random selection
            weighted_numbers = []
            for num, count in number_counts.items():
                weighted_numbers.extend([num] * count)
            
            # Generate predictions using different methods
            prediction_text = f"""
🎯 *Prediksi Angka untuk Periode Berikutnya*

📊 Berdasarkan analisis {len(recent_data)} data terakhir:

1. *Frekuensi Tinggi*: {', '.join(top_numbers[:5])}
2. *Angka Panas*: {', '.join(sorted(hot_numbers)) if hot_numbers else 'Tidak ada data'}
3. *Berdasarkan Tanggal*: {', '.join(sorted(date_based))}
4. *Angka Acak Terbobot*: {self.generate_weighted_number(weighted_numbers)}
5. *Polasilang*: {self.generate_cross_pattern(recent_data)}

💡 *Rekomendasi Kombinasi*:
{self.generate_recommendation(number_counts, hot_numbers, date_based)}

⚠️ *Catatan*: Prediksi ini berdasarkan analisis statistik dan tidak menjamin kemenangan.
"""
            await update.message.reply_text(prediction_text, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error generating prediction: {e}")
            await update.message.reply_text("❌ Terjadi kesalahan saat membuat prediksi.")
    
    def generate_weighted_number(self, weighted_numbers):
        """Generate weighted random number"""
        if not weighted_numbers:
            return "Tidak cukup data"
        return ', '.join(random.sample(weighted_numbers, min(3, len(weighted_numbers))))
    
    def generate_cross_pattern(self, df):
        """Generate cross pattern prediction"""
        try:
            last_results = df.head(5)['Result'].tolist()
            if len(last_results) < 5:
                return "Tidak cukup data"
            
            # Get first digit from each result (pastikan result adalah string)
            cross_numbers = []
            for res in last_results[:3]:
                if isinstance(res, str) and res.strip():
                    cross_numbers.append(res[0])
            
            for res in last_results[3:5]:
                if isinstance(res, str) and res.strip():
                    cross_numbers.append(res[-1])
            
            if not cross_numbers:
                return "Tidak bisa dihitung"
                
            return ', '.join(sorted(set(cross_numbers)))
        
        except Exception as e:
            logger.error(f"Error in cross pattern: {e}")
            return "Tidak bisa dihitung"
    
    def generate_recommendation(self, number_counts, hot_numbers, date_based):
        """Generate number recommendation"""
        # Combine different methods
        top_numbers = [num[0] for num in number_counts.most_common(5)] if number_counts else []
        combined = list(set(top_numbers) | (hot_numbers if hot_numbers else set()) | (date_based if date_based else set()))
        
        if not combined:
            return "Tidak bisa membuat rekomendasi"
        
        # Generate 3 recommended combinations
        recommendations = []
        for _ in range(3):
            rec = random.sample(combined, min(4, len(combined)))
            recommendations.append(''.join(rec))
        
        return '\n'.join([f"- {rec}" for rec in recommendations])
    
    def run(self):
        """Run the bot"""
        application = Application.builder().token(self.bot_token).build()
        
        # Add handlers
        application.add_handler(CommandHandler('start', self.start))
        application.add_handler(CommandHandler('help', self.help_command))
        application.add_handler(CommandHandler('metode', self.metode_command))
        application.add_handler(CommandHandler('analisis', self.analisis_command))
        application.add_handler(CommandHandler('prediksi', self.prediksi_command))
        
        # Run the bot
        logger.info("🤖 Bot Analisis Togel sedang berjalan...")
        application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    try:
        bot = TogelAnalysisBot()
        bot.run()
    except Exception as e:
        logger.error(f"Bot failed to start: {e}")