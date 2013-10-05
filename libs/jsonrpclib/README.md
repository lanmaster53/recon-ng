JSONRPClib
==========
This library is an implementation of the JSON-RPC specification.
It supports both the original 1.0 specification, as well as the 
new (proposed) 2.0 spec, which includes batch submission, keyword
arguments, etc.

It is licensed under the Apache License, Version 2.0
(http://www.apache.org/licenses/LICENSE-2.0.html).

Communication
-------------
Feel free to send any questions, comments, or patches to our Google Group 
mailing list (you'll need to join to send a message): 
http://groups.google.com/group/jsonrpclib

Summary
-------
This library implements the JSON-RPC 2.0 proposed specification in pure Python. 
It is designed to be as compatible with the syntax of xmlrpclib as possible 
(it extends where possible), so that projects using xmlrpclib could easily be 
modified to use JSON and experiment with the differences.

It is backwards-compatible with the 1.0 specification, and supports all of the 
new proposed features of 2.0, including:

* Batch submission (via MultiCall)
* Keyword arguments
* Notifications (both in a batch and 'normal')
* Class translation using the 'jsonclass' key.

I've added a "SimpleJSONRPCServer", which is intended to emulate the 
"SimpleXMLRPCServer" from the default Python distribution.

Requirements
------------
It supports cjson and simplejson, and looks for the parsers in that order 
(searching first for cjson, then for the "built-in" simplejson as json in 2.6+, 
and then the simplejson external library). One of these must be installed to 
use this library, although if you have a standard distribution of 2.6+, you 
should already have one. Keep in mind that cjson is supposed to be the 
quickest, I believe, so if you are going for full-on optimization you may 
want to pick it up.

Installation
------------
You can install this from PyPI with one of the following commands (sudo
may be required):

	easy_install jsonrpclib
	pip install jsonrpclib

Alternatively, you can download the source from the github repository
at http://github.com/joshmarshall/jsonrpclib and manually install it
with the following commands:

	git clone git://github.com/joshmarshall/jsonrpclib.git
	cd jsonrpclib
	python setup.py install

Client Usage
------------

This is (obviously) taken from a console session.

	>>> import jsonrpclib
	>>> server = jsonrpclib.Server('http://localhost:8080')
	>>> server.add(5,6)
	11
	>>> print jsonrpclib.history.request
	{"jsonrpc": "2.0", "params": [5, 6], "id": "gb3c9g37", "method": "add"}
	>>> print jsonrpclib.history.response
	{'jsonrpc': '2.0', 'result': 11, 'id': 'gb3c9g37'}
	>>> server.add(x=5, y=10)
	15
	>>> server._notify.add(5,6)
	# No result returned...
	>>> batch = jsonrpclib.MultiCall(server)
	>>> batch.add(5, 6)
	>>> batch.ping({'key':'value'})
	>>> batch._notify.add(4, 30)
	>>> results = batch()
	>>> for result in results:
	>>> ... print result
	11
	{'key': 'value'}
	# Note that there are only two responses -- this is according to spec.

If you need 1.0 functionality, there are a bunch of places you can pass that 
in, although the best is just to change the value on 
jsonrpclib.config.version:

	>>> import jsonrpclib
	>>> jsonrpclib.config.version
	2.0
	>>> jsonrpclib.config.version = 1.0
	>>> server = jsonrpclib.Server('http://localhost:8080')
	>>> server.add(7, 10)
	17
	>>> print jsonrpclib..history.request
	{"params": [7, 10], "id": "thes7tl2", "method": "add"}
	>>> print jsonrpclib.history.response
	{'id': 'thes7tl2', 'result': 17, 'error': None}
	>>> 

The equivalent loads and dumps functions also exist, although with minor 
modifications. The dumps arguments are almost identical, but it adds three 
arguments: rpcid for the 'id' key, version to specify the JSON-RPC 
compatibility, and notify if it's a request that you want to be a 
notification. 

Additionally, the loads method does not return the params and method like 
xmlrpclib, but instead a.) parses for errors, raising ProtocolErrors, and 
b.) returns the entire structure of the request / response for manual parsing.

SimpleJSONRPCServer
-------------------
This is identical in usage (or should be) to the SimpleXMLRPCServer in the default Python install. Some of the differences in features are that it obviously supports notification, batch calls, class translation (if left on), etc. Note: The import line is slightly different from the regular SimpleXMLRPCServer, since the SimpleJSONRPCServer is distributed within the jsonrpclib library.

	from jsonrpclib.SimpleJSONRPCServer import SimpleJSONRPCServer

	server = SimpleJSONRPCServer(('localhost', 8080))
	server.register_function(pow)
	server.register_function(lambda x,y: x+y, 'add')
	server.register_function(lambda x: x, 'ping')
	server.serve_forever()

Class Translation
-----------------
I've recently added "automatic" class translation support, although it is 
turned off by default. This can be devastatingly slow if improperly used, so 
the following is just a short list of things to keep in mind when using it.

* Keep It (the object) Simple Stupid. (for exceptions, keep reading.)
* Do not require init params (for exceptions, keep reading)
* Getter properties without setters could be dangerous (read: not tested)

If any of the above are issues, use the _serialize method. (see usage below)
The server and client must BOTH have use_jsonclass configuration item on and 
they must both have access to the same libraries used by the objects for 
this to work.

If you have excessively nested arguments, it would be better to turn off the 
translation and manually invoke it on specific objects using 
jsonrpclib.jsonclass.dump / jsonrpclib.jsonclass.load (since the default 
behavior recursively goes through attributes and lists / dicts / tuples).

[test_obj.py]

	# This object is /very/ simple, and the system will look through the 
	# attributes and serialize what it can.
	class TestObj(object):
	    foo = 'bar'

	# This object requires __init__ params, so it uses the _serialize method
	# and returns a tuple of init params and attribute values (the init params
	# can be a dict or a list, but the attribute values must be a dict.)
	class TestSerial(object):
	    foo = 'bar'
	    def __init__(self, *args):
	        self.args = args
	    def _serialize(self):
	        return (self.args, {'foo':self.foo,})

[usage]

	import jsonrpclib
	import test_obj

	jsonrpclib.config.use_jsonclass = True

	testobj1 = test_obj.TestObj()
	testobj2 = test_obj.TestSerial()
	server = jsonrpclib.Server('http://localhost:8080')
	# The 'ping' just returns whatever is sent
	ping1 = server.ping(testobj1)
	ping2 = server.ping(testobj2)
	print jsonrpclib.history.request
	# {"jsonrpc": "2.0", "params": [{"__jsonclass__": ["test_obj.TestSerial", ["foo"]]}], "id": "a0l976iv", "method": "ping"}
	print jsonrpclib.history.result
	# {'jsonrpc': '2.0', 'result': <test_obj.TestSerial object at 0x2744590>, 'id': 'a0l976iv'}
	
To turn on this behaviour, just set jsonrpclib.config.use_jsonclass to True. 
If you want to use a different method for serialization, just set 
jsonrpclib.config.serialize_method to the method name. Finally, if you are 
using classes that you have defined in the implementation (as in, not a 
separate library), you'll need to add those (on BOTH the server and the 
client) using the jsonrpclib.config.classes.add() method. 
(Examples forthcoming.)

Feedback on this "feature" is very, VERY much appreciated.

Why JSON-RPC?
-------------
In my opinion, there are several reasons to choose JSON over XML for RPC:

* Much simpler to read (I suppose this is opinion, but I know I'm right. :)
* Size / Bandwidth - Main reason, a JSON object representation is just much smaller.
* Parsing - JSON should be much quicker to parse than XML.
* Easy class passing with jsonclass (when enabled)

In the interest of being fair, there are also a few reasons to choose XML 
over JSON:

* Your server doesn't do JSON (rather obvious)
* Wider XML-RPC support across APIs (can we change this? :))
* Libraries are more established, i.e. more stable (Let's change this too.)

TESTS
-----
I've dropped almost-verbatim tests from the JSON-RPC spec 2.0 page.
You can run it with:

	python tests.py

TODO
----
* Use HTTP error codes on SimpleJSONRPCServer
* Test, test, test and optimize
