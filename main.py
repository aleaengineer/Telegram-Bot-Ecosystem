import subprocess
import sys
import os
from threading import Thread
import time
import signal
from pathlib import Path

class BotManager:
    def __init__(self):
        self.processes = []
        self.running = True
        
    def run_bot(self, bot_folder, bot_filename):
        """Menjalankan bot dalam folder terpisah"""
        try:
            # Dapatkan path absolut ke folder bot
            bot_path = os.path.abspath(bot_folder)
            bot_file = os.path.join(bot_path, bot_filename)
            
            # Periksa apakah file bot ada
            if not os.path.exists(bot_file):
                print(f"❌ File bot tidak ditemukan: {bot_file}")
                return
                
            print(f"🚀 Menjalankan bot dari: {bot_file}")
            
            # Jalankan bot dengan Python
            process = subprocess.Popen(
                [sys.executable, bot_filename],
                cwd=bot_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            self.processes.append(process)
            
            # Monitor output bot
            while self.running and process.poll() is None:
                try:
                    # Baca output dengan timeout
                    output = process.stdout.readline()
                    if output:
                        print(f"[{bot_folder}] {output.strip()}")
                except Exception as e:
                    print(f"[{bot_folder}] Error reading output: {e}")
                    
                time.sleep(0.1)
                
        except Exception as e:
            print(f"❌ Error menjalankan bot di {bot_folder}: {e}")
    
    def stop_all_bots(self):
        """Menghentikan semua bot"""
        print("\n🛑 Menghentikan semua bot...")
        self.running = False
        
        for process in self.processes:
            try:
                if process.poll() is None:  # Jika process masih berjalan
                    process.terminate()
                    # Tunggu 5 detik untuk graceful shutdown
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        # Jika tidak berhenti dalam 5 detik, paksa kill
                        process.kill()
                        process.wait()
                    print(f"✅ Bot process {process.pid} dihentikan")
            except Exception as e:
                print(f"❌ Error menghentikan process: {e}")
    
    def signal_handler(self, signum, frame):
        """Handler untuk signal interrupt"""
        print(f"\n📡 Menerima signal {signum}")
        self.stop_all_bots()
        sys.exit(0)
    
    def run(self):
        """Menjalankan semua bot"""
        # Setup signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        # Konfigurasi bot
        bots_config = [
            {
                'folder': 'bot1',
                'filename': 'bot1.py',
                'name': 'Data Input Bot'
            },
            {
                'folder': 'bot2', 
                'filename': 'bot2.py',
                'name': 'Togel Analysis Bot'
            }
        ]
        
        # Periksa apakah semua folder dan file bot ada
        missing_bots = []
        for bot in bots_config:
            bot_path = os.path.join(bot['folder'], bot['filename'])
            if not os.path.exists(bot_path):
                missing_bots.append(bot_path)
        
        if missing_bots:
            print("❌ Bot berikut tidak ditemukan:")
            for bot in missing_bots:
                print(f"   - {bot}")
            print("\n💡 Pastikan struktur folder seperti ini:")
            print("   ├── main.py")
            print("   ├── bot1/")
            print("   │   └── bot1.py")
            print("   └── bot2/")
            print("       └── bot2.py")
            return
        
        print("🤖 Bot Manager - Memulai semua bot...")
        print("=" * 50)
        
        # Buat dan jalankan thread untuk setiap bot
        threads = []
        for bot in bots_config:
            print(f"🔄 Mempersiapkan {bot['name']}...")
            thread = Thread(
                target=self.run_bot,
                args=(bot['folder'], bot['filename']),
                name=f"Thread-{bot['name']}",
                daemon=True
            )
            threads.append(thread)
            thread.start()
            time.sleep(2)  # Delay antar bot untuk menghindari konflik
        
        print("=" * 50)
        print("✅ Semua bot telah dimulai!")
        print("📝 Tekan Ctrl+C untuk menghentikan semua bot")
        print("=" * 50)
        
        try:
            # Monitor threads
            while self.running:
                # Periksa apakah ada thread yang mati
                alive_threads = [t for t in threads if t.is_alive()]
                if len(alive_threads) < len(threads):
                    dead_threads = [t for t in threads if not t.is_alive()]
                    for thread in dead_threads:
                        print(f"⚠️  Thread {thread.name} telah berhenti")
                
                time.sleep(5)  # Check setiap 5 detik
                
        except KeyboardInterrupt:
            print("\n⌨️  Keyboard interrupt diterima")
        except Exception as e:
            print(f"\n❌ Error dalam monitoring: {e}")
        finally:
            self.stop_all_bots()
            
            # Tunggu semua thread selesai
            print("⏳ Menunggu semua thread selesai...")
            for thread in threads:
                thread.join(timeout=3)
            
            print("🏁 Semua bot telah dihentikan. Selamat tinggal!")

def main():
    """Fungsi utama"""
    try:
        # Periksa apakah Python version mendukung
        if sys.version_info < (3, 7):
            print("❌ Python 3.7 atau lebih baru diperlukan")
            sys.exit(1)
        
        # Periksa apakah file .env ada (untuk bot)
        env_files = ['.env', 'bot1/.env', 'bot2/.env']
        env_found = any(os.path.exists(env_file) for env_file in env_files)
        
        if not env_found:
            print("⚠️  Peringatan: File .env tidak ditemukan")
            print("   Pastikan konfigurasi environment variables sudah benar")
            print("   untuk TELEGRAM_BOT_TOKEN dan GOOGLE_SPREADSHEET_ID")
            print()
        
        # Jalankan bot manager
        bot_manager = BotManager()
        bot_manager.run()
        
    except Exception as e:
        print(f"❌ Error fatal: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
