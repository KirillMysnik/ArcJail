class CallbackDecorator:
    def __init__(self, callback):
        self.callback = callback
        self.register()

    def __call__(self, *args, **kwargs):
        self.callback(*args, **kwargs)

    def register(self):
        raise NotImplementedError

    def unregister(self):
        raise NotImplementedError
