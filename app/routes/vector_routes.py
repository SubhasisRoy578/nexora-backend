from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def vector_test():
    return {
        "module": "vector routes working"
    }