
import time
import pymongo

EXECUTABLE_MONGO_METHODS = set([typ for typ in dir(pymongo.collection.Collection) if not typ.startswith('_')])
EXECUTABLE_MONGO_METHODS.update(set([typ for typ in dir(pymongo.Connection) if not typ.startswith('_')]))
EXECUTABLE_MONGO_METHODS.update(set([typ for typ in dir(pymongo) if not typ.startswith('_')]))

def safe_mongocall(call):
    """ Decorator for automatic handling of AutoReconnect-exceptions.
    """

    def _safe_mongocall(*args, **kwargs):
        for i in xrange(5):
            try:
                return call(*args, **kwargs)
            except pymongo.errors.AutoReconnect:
                print 'AutoReconnecting, try', i
                time.sleep(pow(2, i))
        print 'Error: Failed operation!'
    return _safe_mongocall


class Executable:
    """ Wrap a MongoDB-method and handle AutoReconnect-exceptions
    using the safe_mongocall decorator.
    """

    def __init__(self, method):
        self.method = method

    @safe_mongocall
    def __call__(self, *args, **kwargs):
        return self.method(*args, **kwargs)


class MongoProxy:
    """ Proxy for MongoDB connection.
    Methods that are executable, i.e find, insert etc, get wrapped in an
    Executable-instance that handles AutoReconnect-exceptions transparently.

    """
    def __init__(self, conn):
        """ conn is an ordinary MongoDB-connection.
        
        """
        self.conn = conn
       
    def __getitem__(self, key):
        """ Create and return proxy around the method in the connection
        named "key".
        
        """
        return MongoProxy(getattr(self.conn, key))
    
    def __getattr__(self, key):
        """ If key is the name of an executable method in the MongoDB connection,
        for instance find or insert, wrap this method in Executable-class that
        handles AutoReconnect-Exception.

        """
        if key in EXECUTABLE_MONGO_METHODS:
            return Executable(getattr(self.conn, key))
        return self[key]

    def __call__(self, *args, **kwargs):
        return self.conn(*args, **kwargs)

    def __dir__(self):
        return dir(self.conn)

    def __repr__(self):
        return self.conn.__repr__()

    def __nonzero__(self):
        return True