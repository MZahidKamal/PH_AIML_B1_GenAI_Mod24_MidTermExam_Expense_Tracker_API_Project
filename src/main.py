# External imports -----------------------------------------------------------------------------------------------------
from fastapi import FastAPI
from contextlib import asynccontextmanager

# Internal imports -----------------------------------------------------------------------------------------------------
from src.core.config import check_env_settings
from src.db.session import check_db_connection, db_engine
from src.core.exceptions import AppException, app_exception_handler
from src.api.v1.api import api_router




# Decorator ------------------------------------------------------------------------------------------------------------

# Define an asynchronous context manager to handle FastAPI application startup and shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    try:

        # Validate and display environment configuration settings during startup
        check_env_settings()

        # Verify the database connection asynchronously during startup
        await check_db_connection()
        print("\nApplication startup checks completed successfully.")

        # Yield control back to the FastAPI application to start accepting requests
        yield

    # Catch any startup or runtime errors
    except Exception as error:
        print(f"Startup failed due to: {error}")

        # Re-raise the error to prevent the application from starting with invalid state
        raise error

    # Execute cleanup tasks during application shutdown
    finally:

        # Close all connections in the database engine pool
        await db_engine.dispose()
        print("Application shutting down...")





# FastAPI main App -----------------------------------------------------------------------------------------------------
# Initialize the FastAPI application instance with a custom project title and the defined lifespan context manager
app = FastAPI(title="PH_AIML_B1_GenAI_Mod24_MidTermExam_Expense_Tracker_API_Project App", lifespan=lifespan)





# Register the global handler that converts every AppException into a JSON error response
app.add_exception_handler(AppException, app_exception_handler)





# Root API Routers -----------------------------------------------------------------------------------------------------
# Mount all version 1 feature routers
app.include_router(api_router)
# app.include_router(api_router, prefix="/api/v1")





# ----------------------------------------------------------------------------------------------------------------------
