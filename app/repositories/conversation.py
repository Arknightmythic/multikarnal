from typing import Optional, List, Tuple
from app.repositories.base import Database
import logging

logger = logging.getLogger("repo.conversation")

class ConversationRepository:
    def get_active_session(self, user_id: str, platform: str) -> Optional[str]:
        try:
            with Database.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT conversation_id
                        FROM active_conversations
                        WHERE platform_unique_id = %s AND platform = %s
                        LIMIT 1
                        """,
                        (user_id, platform)
                    )
                    row = cursor.fetchone()
                    return str(row[0]) if row else None
        except Exception as e:
            logger.error(f"Error fetching session: {e}")
            return None

    def save_session(self, user_id: str, platform: str, conversation_id: str):
        try:
            with Database.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO active_conversations (platform_unique_id, platform, conversation_id, last_active_at)
                        VALUES (%s, %s, %s, NOW())
                        ON CONFLICT (platform_unique_id) 
                        DO UPDATE SET
                            conversation_id = EXCLUDED.conversation_id,
                            last_active_at = NOW()
                        """,
                        (user_id, platform, conversation_id)
                    )
        except Exception as e:
            logger.error(f"Error saving session: {e}")

    def get_stale_sessions(self, seconds: int) -> List[Tuple[str, str, str]]:
        try:
            with Database.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT platform_unique_id, platform, conversation_id
                        FROM active_conversations
                        WHERE last_active_at < NOW() - make_interval(secs => %s)
                        LIMIT 50
                        """,
                        (seconds,)
                    )
                    rows = cursor.fetchall()
                    return [(row[0], row[1], row[2]) for row in rows]
        except Exception as e:
            logger.error(f"Error fetching stale sessions: {e}")
            return []

    def clear_session(self, user_id: str):
        try:
            with Database.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "DELETE FROM active_conversations WHERE platform_unique_id = %s",
                        (user_id,)
                    )
                    logger.info(f"Session cleared for user {user_id} on table active_conversations.")
        except Exception as e:
            logger.error(f"Error clearing session for {user_id}: {e}")