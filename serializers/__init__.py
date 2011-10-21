# -*- coding: utf-8 -*-

# Copyright (c) 2008 Alberto García Hierro <fiam@rm-fr.net>

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

from functools import wraps
from wapi.formatters import get_formatter
from wapi.serializers.decorators import *
from wapi.serializers.serializers import *

def include(obj, method=None, **kwargs):
    return serialization(obj, method, **kwargs)[1]

def include_list(objs, method=None, **kwargs):
    try:
        s = get_object_serialization(objs[0], method)
    except IndexError:
        return []
    return [s.method(obj, **kwargs) for obj in objs]

def chain(obj, method=None, **kwargs):
    serializer = get_class_serializer(obj.__class__)
    data = [serialization(obj, method, **kwargs)]
    if not serializer.__class__.serializes_as_dict:
        # if we serialize it via the default serializer,
        # we only want the result
        return data[0][1]
    else:
        return dict(data)

def proplist(obj, properties):
    return dict([(prop, getattr(obj, prop)) for prop in properties])

def merge(*args, **kwargs):
    """Merges any dictionaries passed as args with kwargs"""
    base = args[0]
    for arg in args[1:]:
        base.update(arg)

    base.update(kwargs)
    return base

def S(**kwargs):
    """Convenience function for creating dictionaries more cleanly"""
    return kwargs

def empty(obj_name):
    return { obj_name: {} }

def get_class_serializer(cls):
    from inspect import getmro
    for cls_profile in getmro(cls):
        if cls_profile in SERIALIZERS_REGISTRY.keys():
            return SERIALIZERS_REGISTRY[cls_profile]

def get_object_serialization(obj, method=None):
    ser = get_class_serializer(obj.__class__)
    return ser._get_serialization(obj, method)

def serialize(format, objs, method=None, out=None, **kwargs):
    fmt = get_formatter(format)(out=out)
    fmt.start()

    if objs is None:
        fmt.none()
    elif len(objs) == 0:
        fmt.empty()
    else:
        fmt.format_list([get_object_serialization(obj, method).apply(obj, **kwargs) for obj in objs])

    fmt.end()
    return fmt.get()

def serialize_one(format, obj, method, out=None, **kwargs):
    fmt = get_formatter(format)(out=out)
    fmt.start()
    if obj is None:
        fmt.none()
    else:
        serialization = get_object_serialization(obj, method)
        fmt.format(serialization.apply(obj, **kwargs))
    fmt.end()
    return fmt.get()

def serialization(obj, method=None, **kwargs):
    return get_object_serialization(obj, method).apply(obj, **kwargs)

