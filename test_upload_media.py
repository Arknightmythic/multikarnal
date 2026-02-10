import requests
import os

# 1. KONFIGURASI (Sesuaikan dengan alamat server Anda)
BASE_URL = "http://172.16.8.108:9798" # Alamat BE Main
ENDPOINT = f"{BASE_URL}/api/live-chat/internal/chat/media"
INTERNAL_KEY = "migas-jaya-jaya-123" # Harus sama dengan INTERNAL_API_KEY di .env BE Main

# 2. DATA TESTING
# Pastikan external_user_id ini sudah memiliki sesi aktif (status 'active' atau 'queued') 
# di tabel live_chat_sessions agar path tersimpan ke database.
test_data = {
    "platform": "whatsapp",
    "external_user_id": "628123456789" # ID unik platform (nomor WA pengirim)
}

# 3. PERSIAPAN FILE DUMMY
dummy_filename = "test_image.jpg"
with open(dummy_filename, "wb") as f:
    f.write(b"\xFF\xD8\xFF\xE0" + b"0" * 100) # Header minimal file JPEG

print(f"--- MENGIRIM MEDIA KE: {ENDPOINT} ---")

try:
    # 4. KIRIM REQUEST (Multipart Form-Data)
    headers = {
        "x-internal-key": INTERNAL_KEY
    }
    
    with open(dummy_filename, "rb") as image_file:
        files = {
            "file": (dummy_filename, image_file, "image/jpeg")
        }
        
        response = requests.post(
            ENDPOINT, 
            data=test_data, 
            files=files, 
            headers=headers,
            timeout=30
        )

    # 5. HASIL RESPONS
    print(f"STATUS CODE: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print("✅ BERHASIL!")
        print(f"URL File: {result.get('url')}")
        print(f"Pesan DB: {result.get('db_message')}")
        
        if not result.get('db_message'):
            print("\n⚠️ PERINGATAN: File terupload tapi GAGAL simpan ke Database.")
            print("Hal ini biasanya karena tidak ditemukan sesi aktif untuk external_user_id tersebut.")
    else:
        print("❌ GAGAL!")
        print(f"Response: {response.text}")

except Exception as e:
    print(f"!!! TERJADI ERROR !!!\n{e}")

finally:
    # Hapus file dummy setelah test
    if os.path.exists(dummy_filename):
        os.remove(dummy_filename)