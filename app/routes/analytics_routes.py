from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def analytics_test():
    return {
        "module": "analytics routes working"
    }