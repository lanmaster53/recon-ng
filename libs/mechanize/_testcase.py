import os
import shutil
import subprocess
import tempfile
import unittest


class SetupStack(object):

    def __init__(self):
        self._on_teardown = []

    def add_teardown(self, teardown):
        self._on_teardown.append(teardown)

    def tear_down(self):
        for func in reversed(self._on_teardown):
            func()


class TearDownConvenience(object):

    def __init__(self, setup_stack=None):
        self._own_setup_stack = setup_stack is None
        if setup_stack is None:
            setup_stack = SetupStack()
        self._setup_stack = setup_stack

    # only call this convenience method if no setup_stack was supplied to c'tor
    def tear_down(self):
        assert self._own_setup_stack
        self._setup_stack.tear_down()


class TempDirMaker(TearDownConvenience):

    def make_temp_dir(self, dir_=None):
        temp_dir = tempfile.mkdtemp(prefix="tmp-%s-" % self.__class__.__name__,
                                    dir=dir_)
        def tear_down():
            shutil.rmtree(temp_dir)
        self._setup_stack.add_teardown(tear_down)
        return temp_dir


class MonkeyPatcher(TearDownConvenience):

    Unset = object()

    def monkey_patch(self, obj, name, value):
        orig_value = getattr(obj, name)
        setattr(obj, name, value)
        def reverse_patch():
            setattr(obj, name, orig_value)
        self._setup_stack.add_teardown(reverse_patch)

    def _set_environ(self, env, name, value):
        if value is self.Unset:
            try:
                del env[name]
            except KeyError:
                pass
        else:
            env[name] = value

    def monkey_patch_environ(self, name, value, env=os.environ):
        orig_value = env.get(name, self.Unset)
        self._set_environ(env, name, value)
        def reverse_patch():
            self._set_environ(env, name, orig_value)
        self._setup_stack.add_teardown(reverse_patch)


class FixtureFactory(object):

    def __init__(self):
        self._setup_stack = SetupStack()
        self._context_managers = {}
        self._fixtures = {}

    def register_context_manager(self, name, context_manager):
        self._context_managers[name] = context_manager

    def get_fixture(self, name, add_teardown):
        context_manager = self._context_managers[name]
        fixture = context_manager.__enter__()
        add_teardown(lambda: context_manager.__exit__(None, None, None))
        return fixture

    def get_cached_fixture(self, name):
        fixture = self._fixtures.get(name)
        if fixture is None:
            fixture = self.get_fixture(name, self._setup_stack.add_teardown)
            self._fixtures[name] = fixture
        return fixture

    def tear_down(self):
        self._setup_stack.tear_down()


class TestCase(unittest.TestCase):

    def setUp(self):
        self._setup_stack = SetupStack()
        self._monkey_patcher = MonkeyPatcher(self._setup_stack)

    def tearDown(self):
        self._setup_stack.tear_down()

    def register_context_manager(self, name, context_manager):
        return self.fixture_factory.register_context_manager(
            name, context_manager)

    def get_fixture(self, name):
        return self.fixture_factory.get_fixture(name, self.add_teardown)

    def get_cached_fixture(self, name):
        return self.fixture_factory.get_cached_fixture(name)

    def add_teardown(self, *args, **kwds):
        self._setup_stack.add_teardown(*args, **kwds)

    def make_temp_dir(self, *args, **kwds):
        return TempDirMaker(self._setup_stack).make_temp_dir(*args, **kwds)

    def monkey_patch(self, *args, **kwds):
        return self._monkey_patcher.monkey_patch(*args, **kwds)

    def monkey_patch_environ(self, *args, **kwds):
        return self._monkey_patcher.monkey_patch_environ(*args, **kwds)

    def assert_contains(self, container, containee):
        self.assertTrue(containee in container, "%r not in %r" %
                        (containee, container))

    def assert_less_than(self, got, expected):
        self.assertTrue(got < expected, "%r >= %r" %
                        (got, expected))


#  http://lackingrhoticity.blogspot.com/2009/01/testing-using-golden-files-in-python.html

class GoldenTestCase(TestCase):

    run_meld = False

    def assert_golden(self, dir_got, dir_expect):
        assert os.path.exists(dir_expect), dir_expect
        proc = subprocess.Popen(["diff", "--recursive", "-u", "-N",
                                 "--exclude=.*", dir_expect, dir_got],
                                stdout=subprocess.PIPE)
        stdout, stderr = proc.communicate()
        if len(stdout) > 0:
            if self.run_meld:
                # Put expected output on the right because that is the
                # side we usually edit.
                subprocess.call(["meld", dir_got, dir_expect])
            raise AssertionError(
                "Differences from golden files found.\n"
                "Try running with --meld to update golden files.\n"
                "%s" % stdout)
        self.assertEquals(proc.wait(), 0)
