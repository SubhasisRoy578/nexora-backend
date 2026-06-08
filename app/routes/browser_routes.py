from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def browser_test():
    return {
        "module": "browser routes working"
    }