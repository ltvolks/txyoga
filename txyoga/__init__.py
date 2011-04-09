# -*- coding: utf-8 -*-
# Copyright (c), 2011, the txYoga authors. See the LICENSE file for details.
"""
Twisted REST object publishing.
"""
from twisted.python.components import registerAdapter
from twisted.web.resource import IResource

from txyoga.interface import ICollection, IElement
from txyoga.resource import CollectionResource, ElementResource


registerAdapter(CollectionResource, ICollection, IResource)
registerAdapter(ElementResource, IElement, IResource)

