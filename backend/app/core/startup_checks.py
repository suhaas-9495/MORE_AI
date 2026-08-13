import sys
import logging

logger = logging.getLogger("moreai")

REQUIRED_ENV_VARS = [
    "GROQ_API_KEY",
    "SECRET_KEY",
]

OPTIONAL_ENV_VARS = {
    "LANGFUSE_PUBLIC_KEY": "Langfuse tracing disabled",
    "AWS_ACCESS_KEY_ID": "AWS S3/Bedrock disabled",
    "GITHUB_TOKEN": "GitHub integration disabled",
}


def validate_environment(settings) -> bool:
    """
    Validates required environment variables on startup.
    Fails fast if critical config is missing.
    Warns if optional integrations are not configured.
    """
    missing_required = []

    for var in REQUIRED_ENV_VARS:
        value = getattr(settings, var.lower(), "")
        if not value:
            missing_required.append(var)

    if missing_required:
        logger.critical(
            f"Missing required environment variables: {missing_required}. "
            f"Set these in .env before starting."
        )
        return False

    for var, message in OPTIONAL_ENV_VARS.items():
        value = getattr(settings, var.lower(), "")
        if not value:
            logger.warning(f"[Optional] {var} not set — {message}")

    logger.info("Environment validation passed")
    return True