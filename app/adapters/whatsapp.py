import re
from app.core.config import settings
from app.adapters.base import BaseAdapter
from app.adapters.utils import split_text_smartly, make_meta_request
import httpx
class WhatsAppAdapter(BaseAdapter):
    def __init__(self):
        self.version = "v24.0"
        self.base_url = f"https://graph.facebook.com/{self.version}/{settings.WHATSAPP_PHONE_NUMBER_ID}/messages"
        self.token = settings.WHATSAPP_ACCESS_TOKEN

    def _convert_markdown(self, text: str) -> str:
        text = re.sub(r'\*\*(.*?)\*\*', r'*\1*', text)
        text = re.sub(r'~~(.*?)~~', r'~\1~', text)
        return text

    def send_message(self, recipient_id: str, text: str, **kwargs):
        if not self.token: return {"success": False, "error": "No token"}

        text = self._convert_markdown(text)
        chunks = split_text_smartly(text, 4096)
        results = []

        for chunk in chunks:
            payload = {
                "messaging_product": "whatsapp",
                "to": recipient_id,
                "type": "text",
                "text": {"body": chunk}
            }
            if kwargs.get("message_id"):
                payload["context"] = {"message_id": kwargs["message_id"]}

            res = make_meta_request("POST", self.base_url, self.token, payload)
            results.append(res)
        
        return {"sent": True, "results": results}

    def send_typing_on(self, recipient_id: str, message_id: str = None):
        if not self.token: return
        
        if message_id:
            payload = {
                "messaging_product": "whatsapp",
                "status": "read",
                "message_id": message_id,
                "typing_indicator":{
                    "type":"text"
                }
            }
            make_meta_request("POST", self.base_url, self.token, payload)

    def mark_as_read(self, message_id: str):
        payload = {
            "messaging_product": "whatsapp",
            "status": "read",
            "message_id": message_id
        }
        make_meta_request("POST", self.base_url, self.token, payload)

    def send_feedback_request(self, recipient_id: str, message_id: str):
        payload = {
            "messaging_product": "whatsapp",
            "to": recipient_id,
            "type": "interactive",
            "interactive": {
                "type": "button",
                "body": {"text": "Apakah jawaban ini membantu?"},
                "action": {
                    "buttons": [
                        {"type": "reply", "reply": {"id": f"like-{message_id}", "title": "Membantu"}},
                        {"type": "reply", "reply": {"id": f"dislike-{message_id}", "title": "Tidak"}}
                    ]
                }
            }
        }
        return make_meta_request("POST", self.base_url, self.token, payload)
    
    # Fungsi Baru: Mendapatkan URL Media dari Meta
    async def get_media_url(self, media_id: str):
        url = f"https://graph.facebook.com/{self.version}/{media_id}"
        headers = {"Authorization": f"Bearer {self.token}"}
        
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, headers=headers)
            if resp.status_code == 200:
                return resp.json().get("url")
        return None

    # Fungsi Baru: Download Binary Content
    async def download_media(self, media_url: str):
        headers = {"Authorization": f"Bearer {self.token}"}
        async with httpx.AsyncClient() as client:
            resp = await client.get(media_url, headers=headers)
            if resp.status_code == 200:
                return resp.content # Binary data
        return None