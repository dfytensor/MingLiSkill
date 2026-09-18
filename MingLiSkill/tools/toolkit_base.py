class Toolkit:
    """Minimal Toolkit base class replacement for standalone use."""
    def __init__(self, name="", tools=None, **kwargs):
        self.name = name
        self._tools = tools or []
    
    def register(self, name=None, description=""):
        def decorator(fn):
            self._tools.append({"name": name or fn.__name__, "fn": fn, "description": description})
            return fn
        return decorator
