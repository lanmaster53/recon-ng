import sys

class LocalClasses(dict):
    def add(self, cls):
        self[cls.__name__] = cls

class Config(object):
    """
    This is pretty much used exclusively for the 'jsonclass' 
    functionality... set use_jsonclass to False to turn it off.
    You can change serialize_method and ignore_attribute, or use
    the local_classes.add(class) to include "local" classes.
    """
    use_jsonclass = True
    # Change to False to keep __jsonclass__ entries raw.
    serialize_method = '_serialize'
    # The serialize_method should be a string that references the
    # method on a custom class object which is responsible for 
    # returning a tuple of the constructor arguments and a dict of
    # attributes.
    ignore_attribute = '_ignore'
    # The ignore attribute should be a string that references the
    # attribute on a custom class object which holds strings and / or
    # references of the attributes the class translator should ignore.
    classes = LocalClasses()
    # The list of classes to use for jsonclass translation.
    version = 2.0
    # Version of the JSON-RPC spec to support
    user_agent = 'jsonrpclib/0.1 (Python %s)' % \
        '.'.join([str(ver) for ver in sys.version_info[0:3]])
    # User agent to use for calls.
    _instance = None
    
    @classmethod
    def instance(cls):
        if not cls._instance:
            cls._instance = cls()
        return cls._instance
