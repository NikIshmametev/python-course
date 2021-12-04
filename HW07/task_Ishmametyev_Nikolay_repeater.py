from functools import wraps

TEXT_BEFORE_FUNC = "before function call"
TEXT_AFTER_FUNC = "after function call"

TEXT_BEFORE_FUNC_IN_CLASS = "class: " + TEXT_BEFORE_FUNC
TEXT_AFTER_FUNC_IN_CLASS = "class: " + TEXT_AFTER_FUNC


def repeater(count):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for _ in range(count):
                func(*args, **kwargs)
        return wrapper
    return decorator


def verbose(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        print(TEXT_BEFORE_FUNC)
        outcome = func(*args, **kwargs)
        print(TEXT_AFTER_FUNC)
        return outcome
    return wrapper


class verbose_context:
    def __call__(self, func):
        @wraps(func)
        def inner(*args, **kwds):
            with self:
                return func(*args, **kwds)
        return inner

    def __enter__(self):
        """Return `self` upon entering the runtime context."""
        print(TEXT_BEFORE_FUNC_IN_CLASS)

    def __exit__(self, exc_type, exc_value, traceback):
        """Raise any exception triggered within the runtime context."""
        print(TEXT_AFTER_FUNC_IN_CLASS)
