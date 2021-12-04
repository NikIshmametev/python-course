class Indenter:
    def __init__(self, indent_str: str = " "*4, indent_level: int = 0):
        self.indent_str = indent_str
        self.indent_level = indent_level - 1

    def print(self, msg):
        """Print msg according to context level"""
        print(self.indent_str * self.indent_level + msg)

    def __enter__(self):
        """Return `self` upon entering the runtime context."""
        self.indent_level += 1
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Raise any exception triggered within the runtime context."""
        self.indent_level -= 1
