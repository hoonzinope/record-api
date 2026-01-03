
class VerifierInterface:
    def verify(self, data):
        """Verify the given data.

        Args:
            data: The data to be verified.

        Returns:
            bool: True if verification is successful, False otherwise.
        """
        raise NotImplementedError("Subclasses must implement this method.")