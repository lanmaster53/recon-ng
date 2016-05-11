from Queue import Queue, Empty
import threading
import time

class ThreadingMixin(object):

    def _thread_wrapper(self, *args):
        ''' Wrapper for the worker method defined in the module. Handles calling the actual worker, cleanly exiting upon
        interrupt, and passing exceptions back to the main process.'''
        thread_name = threading.current_thread().name
        self.debug('THREAD => %s started.' % thread_name)
        while not self.stopped.is_set():
            try:
                # use the get_nowait() method for retrieving a queued item to
                # prevent the thread from blocking when the queue is empty
                obj = self.q.get_nowait()
            except Empty:
                continue
            try:
                # launch the public module_thread method
                self.module_thread(obj, *args)
            except:
                # handle exceptions local to the thread
                self.print_exception('(thread=%s, object=%s)' % (thread_name, repr(obj)))
            finally:
                self.q.task_done()
        self.debug('THREAD => %s exited.' % thread_name)

    # sometimes a keyboardinterrupt causes a race condition between when the self.q.task_done() call above and the
    # self.q.empty() call below, causing all the threads to hang. introducing the time.sleep(.7) call below reduces
    # the likelihood of encountering the race condition.

    def thread(self, *args):
        # disable threading in debug mode
        if self._global_options['verbosity'] >= 2:
            # call the thread method in serial for each input
            for item in args[0]:
                self.module_thread(item, *args[1:])
            return
        # begin threading code
        thread_count = self._global_options['threads']
        self.stopped = threading.Event()
        self.exc_info = None
        self.q = Queue()
        # populate the queue from the user-defined iterable. should be done
        # before the threads start so they have something to process right away
        for item in args[0]:
            self.q.put(item)
        # launch the threads
        threads = []
        for i in range(thread_count):
            t = threading.Thread(target=self._thread_wrapper, args=args[1:])
            threads.append(t)
            t.setDaemon(True)
            t.start()
        # hack to catch keyboard interrupts
        try:
            while not self.q.empty():
                time.sleep(.7)
        except KeyboardInterrupt:
            self.error('Ok. Waiting for threads to exit...')
            # set the event flag to trigger an exit for all threads (interrupt condition)
            self.stopped.set()
            # prevent the module from returning to the interpreter until all threads have exited
            for t in threads:
                t.join()
            raise
        self.q.join()
        # set the event flag to trigger an exit for all threads (normal condition)
        # the threads are no longer needed once all the data has been processed
        self.stopped.set()
