# Field length limits (shared by the SQLAlchemy model and the Pydantic schemas) ----------------------------------------
USERNAME_MIN_LENGTH = 3
USERNAME_MAX_LENGTH = 50
EMAIL_MIN_LENGTH = 6
EMAIL_MAX_LENGTH = 255
HASHED_PASSWORD_MAX_LENGTH = 255



# Username may contain only letters, digits and underscores (no spaces or special characters) --------------------------
USERNAME_PATTERN = r"^[A-Za-z0-9_]+$"





# Error codes returned in error responses ------------------------------------------------------------------------------
USER_NOT_FOUND = "USER_NOT_FOUND"
USERNAME_ALREADY_EXISTS = "USERNAME_ALREADY_EXISTS"
EMAIL_NOT_FOUND = "EMAIL_NOT_FOUND"
EMAIL_ALREADY_EXISTS = "EMAIL_ALREADY_EXISTS"





# ----------------------------------------------------------------------------------------------------------------------
