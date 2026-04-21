# app/services/orchestrator.py

import time
from typing import Dict, Any, List
from app.schemas.models import IncomingMessage
from app.services.chatbot import ChatbotClient
from app.adapters.base import BaseAdapter
from app.repositories.conversation import ConversationRepository
from app.core.config import settings
import logging
import uuid
logger = logging.getLogger("service.orchestrator")

RESET_KEYWORDS: List[str] = [
    "terima kasih", "terimakasih", "makasih", "trimakasih", "trims",
    "thank you", "thankyou", "thanks"
]

class MessageOrchestrator:
    def __init__(
        self, 
        chatbot: ChatbotClient,
        adapters: Dict[str, BaseAdapter]
    ):
        self.chatbot = chatbot
        self.adapters = adapters
        self.repo_conv = ConversationRepository()

    def timeout_session(self, user_id: str, platform: str):
        adapter = self.adapters.get(platform)
        if adapter:
            try:
                timeout_msg = "Sesi Anda telah berakhir. Silakan kirim pesan baru untuk memulai percakapan kembali."
                adapter.send_message(user_id, timeout_msg)
            except Exception as e:
                logger.error(f"Failed to send timeout message to {user_id}: {e}")
        
        self.repo_conv.clear_session(user_id)

    def handle_feedback(self, msg: IncomingMessage):
        return

    # PERUBAHAN UTAMA: Ubah menjadi ASYNC
    async def process_message(self, msg: IncomingMessage):
        adapter = self.adapters.get(msg.platform)
        if not adapter: 
            return

        user_id = msg.platform_unique_id
        
        clean_query = msg.query.strip().lower()
        
        is_reset = any(keyword in clean_query for keyword in RESET_KEYWORDS)

        if is_reset:
            logger.info(f"User {user_id} sent reset keyword. Clearing local session.")
            
            reply_text = "Sama-sama! Senang bisa membantu. Sesi percakapan ini telah di-akhiri."
            # Note: adapter.send_message biasanya sync, tidak perlu await kecuali adapter diubah jadi async
            adapter.send_message(user_id, reply_text)
            
            self.repo_conv.clear_session(user_id)
            return

        current_conv_id = self.repo_conv.get_active_session(user_id, msg.platform)
        
        try:
            msg_id = msg.metadata.get("message_id") if msg.metadata else None
            adapter.send_typing_on(user_id, message_id=msg_id)
            if msg.platform == "whatsapp" and msg_id and hasattr(adapter, 'mark_as_read'):
                adapter.mark_as_read(msg_id)
        except Exception: 
            pass

        if msg.type == "image" and msg.metadata.get("media_id"):
                adapter = self.adapters.get(msg.platform)
                
                # 1. Dapatkan URL Media dari Meta
                media_url = await adapter.get_media_url(msg.metadata.get("media_id"))
                
                if media_url:
                    # 2. Download Gambar
                    image_binary = await adapter.download_media(media_url)
                    
                    if image_binary:
                        # --- PERBAIKAN: Gunakan UUID agar nama file pendek & aman ---
                        short_id = str(uuid.uuid4())[:8] # Ambil 8 karakter acak saja cukup
                        timestamp = int(time.time())
                        
                        # Format: instagram_17382912_ad3f12.jpg
                        safe_filename = f"{msg.platform}_{timestamp}_{short_id}.jpg"
                        # ------------------------------------------------------------

                        # 3. Upload ke BE Main
                        upload_resp = await self.chatbot.upload_media_to_main(
                            file_content=image_binary,
                            filename=safe_filename,
                            user_id=user_id,
                            platform=msg.platform
                        )
                        
                        logger.info(f"Image uploaded to BE Main: {upload_resp}")
                        
                        # 4. Kirim link gambar ke Dify sebagai konteks
                        msg.query = f"[IMAGE_UPLOADED] {upload_resp.get('url')}"

        # PERUBAHAN: Panggil chatbot dengan parameter baru dan AWAIT
        # Parameter: message, conversation_id, user_id, platform, user_name

        if msg.platform == "whatsapp":
            resolved_user_name = user_id
        else:
            resolved_user_name = msg.metadata.get("sender_name", "Unknown")

        resp = await self.chatbot.send_message(
            message=msg.query,
            conversation_id=current_conv_id,
            user_id=user_id,
            platform=msg.platform,
            user_name=resolved_user_name
        )

        logger.info(f"Chatbot response for user {user_id} on {msg.platform}: {resp}")
        
        if "error" in resp:
            # Jika ada error, ambil pesan error atau default answer
            logger.error(f"BE Main Error: {resp.get('error')}")
            fallback_msg = resp.get("answer", "Mohon maaf, sistem sedang sibuk. Silakan coba lagi nanti.")
            adapter.send_message(user_id, fallback_msg)
        else:
            answer = resp.get("answer", "")
            new_conv_id = resp.get("conversation_id")
            
            # 4. Save new ID to DB (penting agar history berlanjut)
            if new_conv_id:
                self.repo_conv.save_session(user_id, msg.platform, new_conv_id)
            
            send_kwargs = {}
            if msg.platform == "email":
                send_kwargs["subject"] = f"Re: {msg.metadata.get('subject', 'Inquiry')}"
                # Handle azure oauth logic if needed
                if settings.EMAIL_PROVIDER == "azure_oauth2":
                    send_kwargs["graph_message_id"] = msg.metadata.get("graph_message_id")
                else:
                    send_kwargs["in_reply_to"] = msg.metadata.get("message_id")

            adapter.send_message(user_id, answer, **send_kwargs)

        try: 
            adapter.send_typing_off(user_id)
        except Exception: 
            pass

    async def send_outbound_message(self, recipient_id: str, message: str, platform: str):
        """
        Mengirim pesan dari Agent (BE Main) ke User (WA/IG).
        """
        adapter = self.adapters.get(platform)
        
        if not adapter:
            logger.error(f"Platform {platform} not supported or adapter not loaded.")
            return {"status": "error", "detail": "Platform not supported"}

        try:
            # Panggil fungsi send_message milik adapter (WA/IG)
            # Note: send_message di adapter Anda bersifat synchronous, 
            # tapi tidak masalah untuk traffic kecil.
            result = adapter.send_message(recipient_id, message)
            
            logger.info(f"Outbound message sent to {platform} ({recipient_id}): {result}")
            return result
        except Exception as e:
            logger.error(f"Failed to send outbound message: {e}")
            raise e