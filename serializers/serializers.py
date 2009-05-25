from django.db import models
from wapi.exceptions import ApiError
from wapi.serializers.decorators import *

SERIALIZERS_REGISTRY = {}

class Serialization(object):
    def __init__(self, name, method):
        self.name = name
        self.method = method
    
    def apply(self, obj, **kwargs):
        data = self.method(obj, **kwargs)
        if isinstance(data, dict):
            return (self.name, data)
        else:
            return (self.name, data)


class NoSerializationMethod(RuntimeError):
    pass

class BaseSerializerType(type):
    def __init__(mcs, name, bases, dct):
        super(BaseSerializerType, mcs).__init__(name, bases, dct)
        if hasattr(mcs, 'serializes'):
            try:
                iter(mcs.serializes)
            except TypeError:
                SERIALIZERS_REGISTRY[mcs.serializes] = mcs()
            else:
                for s in mcs.serializes:
                    SERIALIZERS_REGISTRY[s] = mcs()

class BaseSerializer(object):
    obj_names = {}
    def __init__(self, *args, **kwargs):
        super(BaseSerializer, self).__init__(*args, **kwargs)
        for k, v in self.__class__.__dict__.iteritems():
            if hasattr(v, 'obj_name'):
                self.obj_names[getattr(self, k)] = v.obj_name

    def obj_name(self, func):
        return self.obj_names.get(func, None)

    def default(self, obj, **kw):
        raise NotImplementedError

    def _get_serialization(self, obj, method):
        try:
            m = getattr(self, method or 'default')
        except AttributeError:
            raise NoSerializationMethod('Serialization "%s" is not defined in serializer "%s" for object "%s"' % \
                (method, self.__class__.__name__, obj.__class__.__name__))
        return Serialization(self.obj_name(m) or obj.__class__.__name__.lower(), m)

    def _do_serialization(self, obj, method=None, **kw):
        serialization = self._get_serialization(obj, method)
        return serialization.apply(obj, **kw)

class Serializer(BaseSerializer):
    __metaclass__ = BaseSerializerType
    serializes = object

    def default(self, obj, **kw):
        return u'%s' % obj

import datetime
class DateTimeSerializer(Serializer):
    serializes = datetime.datetime

    def default(self, obj, **kw):
        return obj.strftime('%Y/%m/%d %H:%M:%S')

class ModelSerializer(Serializer):
    serializes = models.Model

    def default(self, obj, **kw):
        from wapi.serializers import chain
        try:
            return dict([(k, chain(v)) for k, v in obj.__dict__.iteritems() if not k.startswith('_')])
        except AttributeError:
            return dict()

class DictSerializer(Serializer):
    serializes = {}.__class__

    def default(self, obj, **kwargs):
        from wapi.serializers import chain
        result = {}
        for k, v in obj.iteritems():
            result[k] = chain(v)
            """FIXME 

               The reason for the check: {'test': 1} would generate
               <dict><test><int /></test></dict> with chaining.
               
               Another 'possible' fix is to modify l:114 to return obj
               instead of dict() which would result in
               <dict><test><int>1</int></test></dict>"""
            if result[k] is None or (len(result[k]) == 1 and \
               (result[k].items()[0][1] is None or \
               len(result[k].items()[0][1]) == 0)):
                result[k] = v
        return result

class ApiErrorSerializer(Serializer):
    serializes = ApiError

    @objname('error')
    def default(self, obj, **kwargs):
        return {'message': obj.message, 'type': obj.__class__.__name__, 'status_code': obj.status_code}

