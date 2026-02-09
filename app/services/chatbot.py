# app/services/chatbot.py

import httpx
import logging
from typing import Dict, Any
from app.core.config import settings

logger = logging.getLogger("service.chatbot")

class ChatbotClient:
    def __init__(self):
        self.api_url = settings.BE_MAIN_URL
        self.headers = {
            "Content-Type": "application/json",
            "x-internal-key": settings.INTERNAL_API_KEY
        }

    # Ubah return type hint menjadi Dict
    async def send_message(self, message: str, conversation_id: str, user_id: str, platform: str, user_name: str = "User") -> Dict[str, Any]:
        payload = {
            "query": message,
            "inputs": {},
            "conversation_id": conversation_id,
            "platform": platform,
            "external_user_id": user_id,
            "user_name": user_name
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    self.api_url, 
                    json=payload, 
                    headers=self.headers, 
                    timeout=120.0
                )
                response.raise_for_status()
                return response.json()
                
            except httpx.RequestError as e:
                logger.error(f"Error communicating with BE Main: {e}")
                return {"error": str(e), "answer": "Maaf, sedang ada gangguan pada sistem AI kami."}
            except Exception as e:
                logger.error(f"Unexpected error in ChatbotService: {e}")
                return {"error": str(e), "answer": "Maaf, terjadi kesalahan yang tidak terduga."}
            

    async def upload_media_to_main(self, file_content: bytes, filename: str, user_id: str, platform: str):
        url = f"{self.api_url.replace('/chat/bot', '/chat/media')}" # Hack sedikit URL-nya atau set di config
        
        # Siapkan Multipart Form Data
        files = {'file': (filename, file_content, 'image/jpeg')} # Mime type bisa dinamis
        data = {
            'platform': platform,
            'external_user_id': user_id
        }
        
        # Header khusus (Internal Key tetap perlu, tapi Content-Type jangan di-set manual saat upload file)
        upload_headers = {"x-internal-key": settings.INTERNAL_API_KEY}

        async with httpx.AsyncClient() as client:
            response = await client.post(url, data=data, files=files, headers=upload_headers)
            return response.json()