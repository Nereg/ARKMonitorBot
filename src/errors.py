class DatabaseStateConflictError(Exception):
    """
    Raised when the database's state conflicts with the operation requested to be carried out.
    """