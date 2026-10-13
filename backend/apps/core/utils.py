import uuid


def generate_uuid7():
    """
    Generate a UUID. 
    For MVP stability, we use standard UUID4 (random).
    This ensures compatibility with Django and PostgreSQL immediately.
    We can switch to strict UUIDv7 later if needed for time-ordering benefits.
    """
    return uuid.uuid4()