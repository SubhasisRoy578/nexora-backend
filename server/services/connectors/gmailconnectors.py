"""
Nexora AI — Gmail Connector
OAuth2-based Gmail integration using Google API.
Stores tokens per-user in Redis for session management.
"""

import base64
import json
from typing import Optional, List, Dict, Any
from email.mime.text import MIMEText
import logging

from app.config import settings

logger = logging.getLogger("nexora.connectors.gmail")


class GmailConnector:
    """
    Gmail integration supporting:
    - List/read messages
    - Send emails
    - Search with Gmail operators
    """

    @staticmethod
    def get_token(user_id: str) -> Optional[str]:
        """Check if user has a stored Gmail OAuth token (stub — implement with Redis)."""
        # In production: return redis.get(f"oauth:gmail:{user_id}")
        return None

    async def _get_service(self, user_id: str):
        """Build an authenticated Gmail service for the user."""
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build

        token_data = self.get_token(user_id)
        if not token_data:
            raise PermissionError("Gmail not connected. Please authorize via OAuth.")

        creds_dict = json.loads(token_data)
        creds = Credentials(
            token=creds_dict["token"],
            refresh_token=creds_dict["refresh_token"],
            token_uri="https://oauth2.googleapis.com/token",
            client_id=settings.GOOGLE_CLIENT_ID,
            client_secret=settings.GOOGLE_CLIENT_SECRET,
        )
        return build("gmail", "v1", credentials=creds)

    async def list_messages(
        self,
        user_id: str,
        max_results: int = 10,
        query: Optional[str] = None,
    ) -> Dict[str, Any]:
        """List Gmail messages with optional search query."""
        try:
            service = await self._get_service(user_id)
            params: Dict[str, Any] = {
                "userId": "me",
                "maxResults": max_results,
            }
            if query:
                params["q"] = query

            result = service.users().messages().list(**params).execute()
            message_ids = result.get("messages", [])

            messages = []
            for msg_ref in message_ids[:max_results]:
                msg = service.users().messages().get(
                    userId="me",
                    id=msg_ref["id"],
                    format="metadata",
                    metadataHeaders=["Subject", "From", "Date"],
                ).execute()

                headers = {h["name"]: h["value"] for h in msg.get("payload", {}).get("headers", [])}
                messages.append({
                    "id": msg["id"],
                    "subject": headers.get("Subject", "(no subject)"),
                    "from": headers.get("From", ""),
                    "date": headers.get("Date", ""),
                    "snippet": msg.get("snippet", ""),
                })

            return {"messages": messages, "total": result.get("resultSizeEstimate", 0)}

        except PermissionError as e:
            return {"error": str(e), "connected": False}
        except Exception as e:
            logger.error(f"Gmail list error: {e}")
            return {"error": str(e)}

    async def get_message(self, user_id: str, message_id: str) -> Dict[str, Any]:
        """Get full content of a Gmail message."""
        try:
            service = await self._get_service(user_id)
            msg = service.users().messages().get(
                userId="me",
                id=message_id,
                format="full",
            ).execute()

            headers = {h["name"]: h["value"] for h in msg.get("payload", {}).get("headers", [])}

            # Extract body
            body = ""
            payload = msg.get("payload", {})
            if "parts" in payload:
                for part in payload["parts"]:
                    if part.get("mimeType") == "text/plain":
                        data = part.get("body", {}).get("data", "")
                        if data:
                            body = base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
                            break
            elif "body" in payload:
                data = payload["body"].get("data", "")
                if data:
                    body = base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")

            return {
                "id": message_id,
                "subject": headers.get("Subject", ""),
                "from": headers.get("From", ""),
                "to": headers.get("To", ""),
                "date": headers.get("Date", ""),
                "body": body[:5000],  # Cap for LLM context
            }
        except Exception as e:
            logger.error(f"Gmail get message error: {e}")
            return {"error": str(e)}

    async def send_email(
        self,
        user_id: str,
        to: str,
        subject: str,
        body: str,
    ) -> Dict[str, Any]:
        """Send an email via Gmail."""
        try:
            service = await self._get_service(user_id)
            message = MIMEText(body)
            message["to"] = to
            message["subject"] = subject

            raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
            result = service.users().messages().send(
                userId="me",
                body={"raw": raw},
            ).execute()

            return {"success": True, "message_id": result["id"]}
        except Exception as e:
            logger.error(f"Gmail send error: {e}")
            return {"error": str(e)}