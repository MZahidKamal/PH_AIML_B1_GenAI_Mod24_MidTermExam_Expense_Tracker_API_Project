# External imports -----------------------------------------------------------------------------------------------------
from fastapi import APIRouter

# Internal imports -----------------------------------------------------------------------------------------------------
from src.features.auth.router import router as auth_router
from src.features.transactions.router import router as transactions_router





# Version 1 router -----------------------------------------------------------------------------------------------------

# Collects all feature routers in one place; main.py only needs to include this one router
api_router = APIRouter()


@api_router.get("/", tags=["Root Api"])
async def root():
    return {
        "message": "Welcome to Expense Tracker API!",
        "status": "healthy",
        "version": "v1.0.0",
        "swagger_documentation": "/docs",
        "redoc_documentation": "/redoc"
    }


api_router.include_router(auth_router)
api_router.include_router(transactions_router)





#-----------------------------------------------------------------------------------------------------------------------
