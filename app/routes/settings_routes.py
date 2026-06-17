from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def settings_test():
    return {
        "module": "settings routes working"
    }