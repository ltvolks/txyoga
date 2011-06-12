# -*- coding: utf-8 -*-
# Copyright (c), 2011, the txYoga authors. See the LICENSE file for details.
"""
Resources providing the REST API to some objects.
"""
from urllib import urlencode
from urlparse import urlsplit, urlunsplit

from twisted.web.resource import IResource, Resource
from twisted.web import http

from txyoga import errors, interface
from txyoga.serializers import EncodingResource, reportErrors


class Created(Resource):
    """
    A resource returned when an element has been successfully created.
    """
    def render(self, request):
        request.setResponseCode(http.CREATED)
        return ""



class Deleted(Resource):
    """
    A resource returned when an element has been successfully deleted.
    """
    def render(self, request):
        request.setResponseCode(http.NO_CONTENT)
        return ""



class CollectionResource(EncodingResource):
    """
    A resource representing a REST collection.
    """
    def __init__(self, collection):
        Resource.__init__(self)
        self._collection = collection


    def getChild(self, path, request):
        """
        Gets the resource for an element in the collection for this resource.

        If this is a DELETE request addressing an element this collection,
        deletes the child.  If it is a PUT request addressing an element in
        this collection which does not exist yet, creates an element
        accessible at the request path.  Otherwise, attempts to return the
        resource for the appropriate addressed child, by accessing that child
        and attempting to adapt it to ``IResource``.

        If that child could not be found, (unless it is being created, of
        course), returns an error page signaling the missing element.

        The case for updating an element is not covered in this method: since
        updating is an operation on elements that already exist, that is
        handled by the corresponding ElementResource.
        """
        try:
            if request.method == "DELETE" and not request.postpath:
                self._collection.removeByIdentifier(path)
                return Deleted()

            return IResource(self._collection[path])
        except KeyError:
            if request.method == 'PUT' and not request.postpath:
                return self._createElement(request, identifier=path)

            return self._missingElement(request, path)


    @reportErrors
    def _createElement(self, request, decoder, identifier=None):
        """
        Attempts to create an element.

        If the request inherently specifies the identifier for the
        element being put (for example, with a PUT request), it is
        specified using the identifier keyword argument. If that
        identifier does not match the identifier of the new element,
        `IdentifierError` is raised.
        """
        state = decoder(request.content)
        element = self._collection.createElementFromState(state)

        if identifier is not None:
            actualIdentifier = getattr(element, element.identifyingAttribute)
            if actualIdentifier != identifier:
                raise errors.IdentifierError(identifier, actualIdentifier)

        self._collection.add(element)
        return Created()

    
    @reportErrors
    def _missingElement(self, request, element):
        """
        Reports client about a missing element.
        """
        raise errors.MissingResourceError("no such element %s" % (element,))


    @reportErrors
    def render_GET(self, request, encoder):
        """
        Displays the collection.

        If the collection is too large to be displayed at once, it
        will display a part of the collection, one page at a
        time. Each page will have links to the previous and next
        pages.
        """
        start, stop = self._getBounds(request)
        url = request.prePathURL()
        prevURL, nextURL = self._getPaginationURLs(url, start, stop)

        elements = self._collection[start:stop]
        attrs = self._collection.exposedElementAttributes
        results = [element.toState(attrs) for element in elements]

        if (stop - start) > len(elements):
            # Not enough elements -> end of the collection
            nextURL = None

        response = {"results": results, "prev": prevURL, "next": nextURL}
        return encoder(response)


    def render_POST(self, request):
        """
        Creates a new element in the collection.
        """
        resource = self._createElement(request)
        return resource.render(request)


    def _getBounds(self, request):
        """
        Gets the start and stop bounds out of the query.
        """
        start = _getBound(request.args, "start")
        stop = _getBound(request.args, "stop", self._collection.pageSize)
        return start, stop


    def _getPaginationURLs(self, thisURL, start, stop):
        """
        Produces the URLs for the next page and the previous one.
        """
        scheme, netloc, path, _, _ = urlsplit(thisURL)
        def buildURL(start, stop):
            query = urlencode([("start", start), ("stop", stop)])
            return urlunsplit((scheme, netloc, path, query, ""))

        pageSize = stop - start

        if pageSize < 0:
            raise errors.PaginationError("Requested page size is negative")

        if pageSize > self._collection.maxPageSize:
            raise errors.PaginationError("Requested page size too large")

        prevStart, prevStop = max(0, start - pageSize), start
        if prevStart != prevStop:
            prevURL = buildURL(prevStart, prevStop)
        else:
            prevURL = None

        nextURL = buildURL(stop, stop + pageSize)

        return prevURL, nextURL



def _getBound(args, key, default=0):
    """
    Gets a particular start or stop bound from the given args.
    """
    try:
        values = args[key]
        if len(values) != 1:
            raise errors.PaginationError("duplicate key %s in query" % (key,))

        return int(values[0])
    except KeyError:
        return default
    except ValueError:
        raise errors.PaginationError("key %s not an integer" % (key,))



class ElementResource(EncodingResource):
    """
    A resource representing an element in a collection.
    """
    def __init__(self, element):
        Resource.__init__(self)

        self._element = element

        for childName in element.children:
            child = getattr(element, childName)
            self.putChild(childName, IResource(child))


    @reportErrors
    def render_GET(self, request, encoder):
        """
        Displays the element.
        """
        state = self._element.toState()
        return encoder(state)


    @reportErrors
    def render_PUT(self, request, decoder):
        """
        Updates the element.
        """
        state = decoder(request.content)
        self._element.update(state)
        return ""
