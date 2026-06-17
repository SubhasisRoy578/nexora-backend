"""
Nexora AI — Connectors Router
OAuth-based integrations: Gmail, Google Drive, Notion, Slack, GitHub.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional

from app.models.user import User
from app.middleware.auth_middleware import get_current_user
from app.services.connectors.gmail_connector import GmailConnector
from app.services.connectors.gdrive_connector import GDriveConnector
from app.services.connectors.notion_connector import NotionConnector
from app.services.connectors.slack_connector import SlackConnector
from app.services.connectors.github_connector import GitHubConnector

router = APIRouter()


# ── Gmail ─────────────────────────────────────────────────────────────────────

@router.get("/gmail/messages")
async def list_gmail_messages(
    max_results: int = Query(10, ge=1, le=50),
    query: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
):
    """List recent Gmail messages. Supports Gmail search operators."""
    connector = GmailConnector()
    return await connector.list_messages(
        user_id=str(current_user.id),
        max_results=max_results,
        query=query,
    )


@router.get("/gmail/messages/{message_id}")
async def get_gmail_message(
    message_id: str,
    current_user: User = Depends(get_current_user),
):
    """Get a specific Gmail message by ID."""
    connector = GmailConnector()
    return await connector.get_message(
        user_id=str(current_user.id),
        message_id=message_id,
    )


@router.post("/gmail/send")
async def send_gmail(
    to: str,
    subject: str,
    body: str,
    current_user: User = Depends(get_current_user),
):
    """Send an email via Gmail."""
    connector = GmailConnector()
    return await connector.send_email(
        user_id=str(current_user.id),
        to=to,
        subject=subject,
        body=body,
    )


# ── Google Drive ──────────────────────────────────────────────────────────────

@router.get("/gdrive/files")
async def list_drive_files(
    max_results: int = Query(20, ge=1, le=100),
    query: Optional[str] = None,
    current_user: User = Depends(get_current_user),
):
    """List files in Google Drive."""
    connector = GDriveConnector()
    return await connector.list_files(
        user_id=str(current_user.id),
        max_results=max_results,
        query=query,
    )


@router.get("/gdrive/files/{file_id}/content")
async def get_drive_file_content(
    file_id: str,
    current_user: User = Depends(get_current_user),
):
    """Get text content of a Google Drive file for AI analysis."""
    connector = GDriveConnector()
    return await connector.get_file_content(
        user_id=str(current_user.id),
        file_id=file_id,
    )


# ── Notion ────────────────────────────────────────────────────────────────────

@router.get("/notion/pages")
async def list_notion_pages(
    query: Optional[str] = None,
    current_user: User = Depends(get_current_user),
):
    """Search and list Notion pages."""
    connector = NotionConnector()
    return await connector.search_pages(
        user_id=str(current_user.id),
        query=query,
    )


@router.get("/notion/pages/{page_id}")
async def get_notion_page(
    page_id: str,
    current_user: User = Depends(get_current_user),
):
    """Get content of a specific Notion page."""
    connector = NotionConnector()
    return await connector.get_page_content(
        user_id=str(current_user.id),
        page_id=page_id,
    )


@router.post("/notion/pages")
async def create_notion_page(
    title: str,
    content: str,
    database_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
):
    """Create a new Notion page."""
    connector = NotionConnector()
    return await connector.create_page(
        user_id=str(current_user.id),
        title=title,
        content=content,
        database_id=database_id,
    )


# ── Slack ─────────────────────────────────────────────────────────────────────

@router.get("/slack/channels")
async def list_slack_channels(
    current_user: User = Depends(get_current_user),
):
    """List Slack channels."""
    connector = SlackConnector()
    return await connector.list_channels(user_id=str(current_user.id))


@router.get("/slack/channels/{channel_id}/messages")
async def get_slack_messages(
    channel_id: str,
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
):
    """Get messages from a Slack channel."""
    connector = SlackConnector()
    return await connector.get_messages(
        user_id=str(current_user.id),
        channel_id=channel_id,
        limit=limit,
    )


@router.post("/slack/messages")
async def send_slack_message(
    channel: str,
    text: str,
    current_user: User = Depends(get_current_user),
):
    """Send a message to a Slack channel."""
    connector = SlackConnector()
    return await connector.send_message(
        user_id=str(current_user.id),
        channel=channel,
        text=text,
    )


# ── GitHub ────────────────────────────────────────────────────────────────────

@router.get("/github/repos")
async def list_github_repos(
    current_user: User = Depends(get_current_user),
):
    """List GitHub repositories."""
    connector = GitHubConnector()
    return await connector.list_repos(user_id=str(current_user.id))


@router.get("/github/repos/{owner}/{repo}/issues")
async def list_github_issues(
    owner: str,
    repo: str,
    state: str = "open",
    current_user: User = Depends(get_current_user),
):
    """List GitHub issues for a repository."""
    connector = GitHubConnector()
    return await connector.list_issues(
        user_id=str(current_user.id),
        owner=owner,
        repo=repo,
        state=state,
    )


@router.get("/github/repos/{owner}/{repo}/code")
async def search_github_code(
    owner: str,
    repo: str,
    query: str = Query(..., min_length=1),
    current_user: User = Depends(get_current_user),
):
    """Search code in a GitHub repository."""
    connector = GitHubConnector()
    return await connector.search_code(
        user_id=str(current_user.id),
        owner=owner,
        repo=repo,
        query=query,
    )


# ── Status ────────────────────────────────────────────────────────────────────

@router.get("/status")
async def connector_status(current_user: User = Depends(get_current_user)):
    """Get connection status of all integrations for the current user."""
    return {
        "gmail": {"connected": bool(GmailConnector.get_token(str(current_user.id)))},
        "google_drive": {"connected": bool(GDriveConnector.get_token(str(current_user.id)))},
        "notion": {"connected": bool(NotionConnector.get_token(str(current_user.id)))},
        "slack": {"connected": bool(SlackConnector.get_token(str(current_user.id)))},
        "github": {"connected": bool(GitHubConnector.get_token(str(current_user.id)))},
    }