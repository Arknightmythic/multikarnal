# app/adapters/instagram.py

import re
import logging
import httpx
from typing import Dict, Any, Optional
from app.core.config import settings
from app.adapters.base import BaseAdapter
from app.adapters.utils import split_text_smartly, make_meta_request
from app.schemas.models import IncomingMessage # Pastikan import ini ada

logger = logging.getLogger("adapters.instagram")

class InstagramAdapter(BaseAdapter):
    def __init__(self):
        self.version = "v24.0"
        self.base_url = f"https://graph.instagram.com/{self.version}/{settings.INSTAGRAM_CHATBOT_ID}/messages"
        self.token = settings.INSTAGRAM_PAGE_ACCESS_TOKEN

    def _clean_id(self, user_id: str) -> str:
        return user_id.replace('@instagram.com', '').strip()

    # --- IMPLEMENTASI BARU: Parsing Webhook (Wajib untuk menerima pesan) ---
    def parse_webhook_payload(self, payload: Dict[str, Any]) -> Optional[IncomingMessage]:
        """
        Menerjemahkan JSON Webhook Instagram menjadi IncomingMessage standar.
        """
        try:
            if "entry" not in payload or not payload["entry"]:
                return None
            entry = payload.get("entry", [])[0]
            
            if "messaging" not in entry or not entry["messaging"]:
                return None
            messaging = entry.get("messaging", [])[0]
            
            sender_id = messaging.get("sender", {}).get("id")
            if messaging.get("message", {}).get("is_echo"):
                logger.info("Ignoring echo message from Instagram.")
                return None

            # 2. Cek apakah sender_id sama dengan ID Halaman/Bot kita sendiri
            sender_id = messaging.get("sender", {}).get("id")
            if sender_id == settings.INSTAGRAM_PAGE_ID: # Pastikan Anda punya setting ini
                logger.info("Ignoring message from self.")
                return None
            
            if not sender_id:
                return None
            
            # Cek tipe pesan
            if "message" in messaging:
                message_data = messaging["message"]
                msg_id = message_data.get("mid")
                
                # 1. Cek Attachment Gambar
                if "attachments" in message_data:
                    for attachment in message_data["attachments"]:
                        if attachment["type"] == "image":
                            # Instagram langsung memberikan URL di webhook payload
                            image_url = attachment["payload"].get("url")
                            
                            return IncomingMessage(
                                platform="instagram",
                                platform_unique_id=sender_id,
                                type="image",
                                query="[IMAGE]", # Placeholder text
                                metadata={
                                    "message_id": msg_id,
                                    "media_id": image_url, # Simpan URL di sini untuk diambil get_media_url nanti
                                    "sender_name": "Instagram User" # IG API standar jarang kasih nama di webhook event ini
                                }
                            )

                # 2. Cek Text Biasa
                text = message_data.get("text", "")
                if text:
                    return IncomingMessage(
                        platform="instagram",
                        platform_unique_id=sender_id,
                        type="text",
                        query=text,
                        metadata={
                            "message_id": msg_id,
                            "sender_name": "Instagram User"
                        }
                    )
            
            return None
            
        except Exception as e:
            logger.error(f"Error parsing Instagram payload: {e}")
            return None

    # --- IMPLEMENTASI BARU: Download & Get URL (Dipanggil oleh Orchestrator) ---
    
    async def get_media_url(self, media_id: str) -> Optional[str]:
        """
        Untuk Instagram, media_id yang kita simpan di metadata SUDAH berupa URL.
        Jadi kita cukup mengembalikannya.
        """
        return media_id

    async def download_media(self, url: str) -> Optional[bytes]:
        """
        Mendownload file gambar dari URL CDN Instagram.
        """
        if not url:
            return None
            
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, timeout=30.0)
                if response.status_code == 200:
                    return response.content
                else:
                    logger.error(f"Failed to download IG media. Status: {response.status_code}")
                    return None
            except Exception as e:
                logger.error(f"Error downloading IG media: {e}")
                return None

    # --- FUNGSI LAMA (Pengiriman Pesan) ---

    def send_typing_on(self, recipient_id: str, message_id: str = None):
        if not self.token: return
        payload = {"recipient": {"id": self._clean_id(recipient_id)}, "sender_action": "typing_on"}
        make_meta_request("POST", self.base_url, self.token, payload)

    def send_typing_off(self, recipient_id: str):
        if not self.token: return
        payload = {"recipient": {"id": self._clean_id(recipient_id)}, "sender_action": "typing_off"}
        make_meta_request("POST", self.base_url, self.token, payload)

    def send_message(self, recipient_id: str, text: str, **kwargs):
        if not self.token: return {"success": False}
        
        # Bersihkan format bold markdown yang mungkin tidak didukung penuh
        text = re.sub(r'\*\*(.*?)\*\*', r'*\1*', text)
        chunks = split_text_smartly(text, 1000)
        
        results = []
        for chunk in chunks:
            payload = {
                "recipient": {"id": self._clean_id(recipient_id)},
                "message": {"text": chunk}
            }
            res = make_meta_request("POST", self.base_url, self.token, payload)
            results.append(res)
            
        return {"sent": True, "results": results}

    def send_feedback_request(self, recipient_id: str, message_id: str):
        if not self.token: return {"success": False}
        
        payload = {
            "recipient": {"id": self._clean_id(recipient_id)},
            "message": {
                "text": "Apakah jawaban ini membantu?",
                "quick_replies": [
                    {"content_type": "text", "title": "Membantu", "payload": f"like-{message_id}"},
                    {"content_type": "text", "title": "Tidak", "payload": f"dislike-{message_id}"}
                ]
            }
        }
        return make_meta_request("POST", self.base_url, self.token, payload)