# -*- coding: utf-8 -*-
# Copyright (c), 2011, the txYoga authors. See the LICENSE file for details.
"""
Serializable REST errors.
"""
from zope.interface import implements

from twisted.web import http

from txyoga import interface


class SerializableError(Exception):
    """
    An error that can be serialized.
    """
    implements(interface.ISerializableError)
    responseCode = http.BAD_REQUEST

    def __init__(self, message, details=None):
        self.message = message
        self.details = details if details is not None else {}



class UnsupportedContentTypeError(SerializableError):
    """
    Raised when the provided content type is unsupported.

    This happens on POST or PUT.
    """
    responseCode = http.UNSUPPORTED_MEDIA_TYPE

    def __init__(self, supportedContentTypes, providedContentType):
        message = "no acceptable decoder available for given content type"
        details = {"supportedContentTypes": supportedContentTypes,
                   "providedContentType": providedContentType}
        SerializableError.__init__(self, message, details)



class MissingContentType(SerializableError):
    """
    Raised when the client failed to specify the content type.
    """
    responseCode = http.UNSUPPORTED_MEDIA_TYPE

    def __init__(self, supportedContentTypes):
        message = "request didn't specify a content type"
        details = {"supportedContentTypes": supportedContentTypes}
        SerializableError.__init__(self, message, details)



class UnacceptableRequestError(SerializableError):
    """
    Raised when the requested resource could not be provided in one of the
    accepted content types.

    This happens on GET.
    """
    responseCode = http.NOT_ACCEPTABLE

    def __init__(self, supportedContentTypes, acceptedContentTypes):
        message = "no acceptable encoder available"
        details = {"supportedContentTypes": supportedContentTypes,
                   "acceptedContentTypes": acceptedContentTypes}
        SerializableError.__init__(self, message, details)



class PaginationError(SerializableError):
    """
    Raised when there was a problem computing pagination.
    """



class MissingResourceError(SerializableError):
    """
    Raised when attempting to access a resource that does not exist.
    """
    responseCode = http.NOT_FOUND



UNSPECIFIED = object()



class AttributeValueUpdateError(SerializableError):
    """
    Raised when attempting to update an element with some state that
    has at least one immutable (non-updatable) attribute with a
    different value than that in the existing element.
    """
    responseCode = http.FORBIDDEN

    def __init__(self, attribute, newValue, currentValue=UNSPECIFIED):
        message = ("attribute update not allowed and provided value differs"
                   " from existing value, update aborted")
        details = {"attribute": attribute, "newValue": newValue}
        if currentValue is not UNSPECIFIED:
            details["currentValue"] = currentValue
        SerializableError.__init__(self, message, details)



class IdentifierError(SerializableError):
    """
    Raised when attempting to put an element somewhere that does not
    match its identification.
    """
    responseCode = http.FORBIDDEN

    def __init__(self, expected, actual):
        message = "new element did not have specified identifying attribute"
        details = {"actualIdentifyingAttribute": repr(actual),
                   "expectedIdentifyingAttribute": repr(expected)}
        SerializableError.__init__(self, message, details)
