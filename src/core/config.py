# External imports -----------------------------------------------------------------------------------------------------
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator





# Necessary classes, objects and functions -----------------------------------------------------------------------------

class EnvSettings(BaseSettings):

    # Supabase Database variables:
    sb_connection_string: str

    # Supabase Database Connection parameters:
    sb_host: str
    sb_port: int
    sb_database: str
    sb_user: str
    sb_password: str


    # Supabase Test Database variables:
    sb_testdb_connection_string: str

    # Supabase Database Connection parameters:
    sb_testdb_host: str
    sb_testdb_port: int
    sb_testdb_database: str
    sb_testdb_user: str
    sb_testdb_password: str


    # JWT variables
    secret_key: str
    algorithm: str
    access_token_expire_minutes: int
    refresh_token_expire_days: int


    # Load environment variables from .env file and ignore extra fields
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


    # Apply the validator to both production and test database connection string fields
    @field_validator("sb_connection_string", "sb_testdb_connection_string")
    @classmethod
    # Define a class method to update the connection string for the psycopg driver
    def use_async_psycopg_driver(cls, connection_string: str) -> str:

        # Check if the connection string starts with the standard postgresql protocol
        if connection_string.startswith("postgresql://"):

            # Replace the standard protocol with the modern psycopg driver protocol
            return connection_string.replace("postgresql://", "postgresql+psycopg://", 1)

        # Return the original connection string if it doesn't match the condition
        return connection_string


env_settings = EnvSettings()





# Checking .env file accessibility -------------------------------------------------------------------------------------

# Define a function to verify and print loaded environment variables
def check_env_settings():
    print("\nChecking if .env variables are loaded correctly...")

    # Iterate through all configuration fields and their values
    for field_name, value in env_settings.model_dump().items():
        value_str = str(value)

        # Mask sensitive information like passwords, secrets, and connection strings for secure display
        if any(kw in field_name.lower() for kw in ("string", "host", "port", "user", "password", "pass", "secret", "algorithm")):
            display_value = "*" * len(value_str)
        else:
            display_value = value_str

        # Print each field name and its corresponding (masked or plain) value
        print(f"    ✅ {field_name.upper():<30}: {display_value}")


# Execute the verification function when the script is run directly
if __name__ == "__main__":
    check_env_settings()





# ----------------------------------------------------------------------------------------------------------------------
