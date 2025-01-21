class InvalidLinkError(Exception):
    """Exception raised for invalid download links."""
    def __init__(self, message="Invalid download link provided."):
        self.message = message
        super().__init__(self.message)