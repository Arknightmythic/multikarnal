from typing import Dict, Any, Optional, Tuple
from app.schemas.models import IncomingMessage
from app.core.config import settings

def parse_whatsapp_payload(data: Dict[str, Any]) -> Optional[IncomingMessage]:
    try:
        entry = data.get("entry", [])[0]
        changes = entry.get("changes", [])[0]
        value = changes.get("value", {})
        
        if "messages" not in value:
            return None
            
        message = value["messages"][0]
        sender_id = message.get("from")
        msg_id = message.get("id") 
        sender_name = value.get("contacts", [{}])[0].get("profile", {}).get("name", "Unknown")

        if str(sender_id) == str(settings.WHATSAPP_PHONE_NUMBER_ID):
            return None

        msg_type = message.get("type")
        
        # --- LOGIC TEXT ---
        if msg_type == "text":
            return IncomingMessage(
                platform_unique_id=sender_id,
                query=message["text"]["body"],
                platform="whatsapp",
                type="text",
                metadata={"phone": sender_id, "message_id": msg_id, "sender_name": sender_name}
            )
        
        # --- LOGIC GAMBAR (BARU) ---
        elif msg_type == "image":
            image_data = message.get("image", {})
            media_id = image_data.get("id")
            caption = image_data.get("caption", "") # Bisa kosong
            
            return IncomingMessage(
                platform_unique_id=sender_id,
                query=caption if caption else "[IMAGE SENT]", # Gunakan caption jika ada, atau placeholder
                platform="whatsapp",
                type="image",
                metadata={
                    "phone": sender_id, 
                    "message_id": msg_id, 
                    "media_id": media_id,
                    "sender_name": sender_name
                }
            )
            
        # --- LOGIC INTERACTIVE (BUTTON) ---
        elif msg_type == "interactive":
            interactive = message.get("interactive", {})
            if interactive.get("type") == "button_reply":
                btn_id = interactive["button_reply"]["id"]
                return IncomingMessage(
                    platform_unique_id=sender_id,
                    query=f"FEEDBACK_EVENT:{btn_id}",
                    platform="whatsapp",
                    type="text",
                    metadata={"is_feedback": True, "payload": btn_id, "message_id": msg_id, "sender_name": sender_name}
                )
                
    except (IndexError, KeyError, AttributeError):
        pass
    return None

def parse_instagram_payload(data: Dict[str, Any]) -> Optional[IncomingMessage]:
    try:
        entry = data.get("entry", [])[0]
        messaging = entry.get("messaging", [])[0]
        
        sender_id = messaging.get("sender", {}).get("id")
        
        if str(sender_id) == str(settings.INSTAGRAM_CHATBOT_ID):
            return None

        message = messaging.get("message", {})
        msg_id = message.get("mid") 
        
        if "quick_reply" in message:
            payload = message["quick_reply"].get("payload")
            return IncomingMessage(
                platform_unique_id=sender_id,
                query=f"FEEDBACK_EVENT:{payload}",
                platform="instagram",
                metadata={"is_feedback": True, "payload": payload, "message_id": msg_id}
            )

        if "text" in message:
            if message.get("is_echo"): return None
            return IncomingMessage(
                platform_unique_id=sender_id,
                query=message["text"],
                platform="instagram",
                metadata={"message_id": msg_id}
            )
            
    except (IndexError, KeyError, AttributeError):
        pass
    return None