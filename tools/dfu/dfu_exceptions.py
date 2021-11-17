class DfuException(Exception):
    """
    Note: Original classname NordicSemiException.
    Exception used as based exception for other exceptions defined in this package.
    """

    def __init__(self, msg, error_code=None):
        super(DfuException, self).__init__(msg)
        self.msg = msg
        self.error_code = error_code


class NotImplementedException(DfuException):
    """
    Exception used when functionality has not been implemented yet.
    """

    pass


class InvalidArgumentException(DfuException):
    """"
    Exception used when a argument is of wrong type
    """

    pass


class MissingArgumentException(DfuException):
    """"
    Exception used when a argument is missing
    """

    pass


class IllegalStateException(DfuException):
    """"
    Exception used when program is in an illegal state
    """

    pass

class ValidationException(DfuException):
    """"
    Exception used when validation failed
    """
    pass