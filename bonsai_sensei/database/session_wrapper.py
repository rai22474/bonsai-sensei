from functools import wraps

def with_session(func):
    """
    Decorator that handles session management.
    It expects 'create_session' to be passed as a keyword argument (e.g. via partial),
    creates a session context, and injects the 'session' object into the decorated function.
    automatically commits the transaction if no exception occurs.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        create_session = kwargs.pop('create_session', None)
        if not create_session:
            raise ValueError("create_session factory must be provided to the decorated function")
        
        with create_session() as session:
            try:
                result = func(session, *args, **kwargs)
                session.commit()
                
                if result and hasattr(result, "id"): 
                     session.refresh(result)
                
                return result
            except Exception:
                session.rollback()
                raise
    return wrapper
