"""
Nexora AI — Auth Middleware
Verifies Clerk JWT tokens and loads the current user.
Works as a FastAPI dependency injected into every protected route.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from clerk_backend_api import Clerk
from clerk_backend_api.jwks_helpers import AuthenticateRequestOptions
import logging
from typing import Optional

from app.config import settings
from app.database import get_postgres_db
from app.models.user import User, UserProfile

logger = logging.getLogger("nexora.auth")

security = HTTPBearer(auto_error=False)
clerk_client = Clerk(bearer_auth=settings.CLERK_SECRET_KEY)


async def verify_clerk_token(token: str) -> Optional[dict]:
    """Verify a Clerk JWT and return the payload."""
    try:
        # Use Clerk SDK to verify the session token
        from jose import jwt, jwk, JWTError
        import httpx

        # Fetch JWKS from Clerk
        jwks_url = f"https://{settings.CLERK_PUBLISHABLE_KEY.replace('pk_test_', '').replace('pk_live_', '')}.clerk.accounts.dev/.well-known/jwks.json"

        async with httpx.AsyncClient() as client:
            resp = await client.get(jwks_url)
            jwks = resp.json()

        # Decode token header to get key ID
        header = jwt.get_unverified_header(token)
        kid = header.get("kid")

        # Find matching key
        matching_key = None
        for key_data in jwks.get("keys", []):
            if key_data.get("kid") == kid:
                matching_key = key_data
                break

        if not matching_key:
            raise HTTPException(status_code=401, detail="JWT key not found")

        # Verify and decode
        public_key = jwk.construct(matching_key)
        payload = jwt.decode(
            token,
            public_key.to_pem().decode(),
            algorithms=["RS256"],
            options={"verify_aud": False},
        )
        return payload

    except Exception as e:
        logger.warning(f"Token verification failed: {e}")
        return None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_postgres_db),
) -> User:
    """
    FastAPI dependency — extracts and validates the current user.
    Inject this into any route that requires authentication.
    
    Usage:
        @router.get("/protected")
        async def protected(user: User = Depends(get_current_user)):
            ...
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    payload = await verify_clerk_token(token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    clerk_user_id = payload.get("sub")
    if not clerk_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing subject claim",
        )

    # Load or auto-create user
    result = await db.execute(
        select(User).where(User.clerk_user_id == clerk_user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        # First login — auto-provision user record
        user = await _create_user_from_clerk(db, clerk_user_id, payload)

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is suspended",
        )

    return user


async def _create_user_from_clerk(
    db: AsyncSession,
    clerk_user_id: str,
    payload: dict,
) -> User:
    """Auto-create a user record on first login from Clerk JWT claims."""
    from app.models.user import UserProfile

    email = payload.get("email", "")

    user = User(
        clerk_user_id=clerk_user_id,
        email=email,
        full_name=payload.get("name"),
        avatar_url=payload.get("picture"),
    )
    db.add(user)
    await db.flush()  # get the user.id

    # Create default profile
    profile = UserProfile(user_id=user.id)
    db.add(profile)
    await db.commit()
    await db.refresh(user)

    logger.info(f"✅ Auto-created user {user.id} for Clerk ID {clerk_user_id}")
    return user


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_postgres_db),
) -> Optional[User]:
    """Like get_current_user but returns None instead of raising for unauthenticated requests."""
    if not credentials:
        return None
    try:
        return await get_current_user(credentials, db)
    except HTTPException:
        return None


def require_subscription(min_tier: str = "pro"):
    """
    Dependency factory — enforces subscription tier.
    Usage: Depends(require_subscription("pro"))
    """
    async def _check(user: User = Depends(get_current_user)) -> User:
        tier_order = {"free": 0, "pro": 1, "team": 2, "enterprise": 3}
        user_level = tier_order.get(user.subscription_tier.value, 0)
        required_level = tier_order.get(min_tier, 1)

        if user_level < required_level:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail=f"This feature requires a {min_tier} subscription.",
            )
        return user

    return _check