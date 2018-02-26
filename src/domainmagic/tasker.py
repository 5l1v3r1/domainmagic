# -*- coding: UTF-8 -*-
import time
from domainmagic.threadpool import ThreadPool


class Task(object):

    """Default task object used by the threadpool
    """

    def __init__(self, method, args=None, kwargs=None):
        self.method = method

        if args is not None:
            self.args = args
        else:
            self.args = ()

        if kwargs is not None:
            self.kwargs = kwargs
        else:
            self.kwargs = {}

        self.done = False
        """will be set to true after the task has been executed"""

        self.result = None
        """contains the result of the method call after the task has been executed"""

    def handlesession(self, worker):
        self.result = self.method(*self.args, **self.kwargs)
        self.done = True

    def __repr__(self):
        return "<Task method='%s' args='%s' kwargs='%s' done=%s >" % (self.method, self.args, self.kwargs, self.done)


class TimeOut(Exception):
    pass


class TaskGroup(object):

    """Similar to Task, but can be used to run multiple methods in parallel
    """

    def __init__(self):
        self.tasks = []

    def add_task(self, method, args=None, kwargs=None):
        """add a method call to the task group. and return the task object.
        the resulting task object should *not* be modified by the caller
        and should not be added to a threadpool again, this will be done automatically when the taskgroup is added to the threadpool
        """
        t = Task(method, args=args, kwargs=kwargs)
        self.tasks.append(t)
        return t

    def handlesession(self, worker):
        """add all tasks to the thread pool"""
        for task in self.tasks:
            worker.pool.add_task(task)

    def join(self, timeout=None):
        """block until all tasks in this group are done"""
        starttime = time.time()
        while True:
            if timeout is not None:
                if time.time() - starttime > timeout:
                    raise TimeOut()

            if self.all_done():
                return
            time.sleep(0.01)

    def all_done(self):
        for task in self.tasks:
            if not task.done:
                return False
        return True


default_threadpool = None


def get_default_threadpool():
    global default_threadpool
    if default_threadpool is None:
        default_threadpool = ThreadPool(
            minthreads=20,
            maxthreads=100,
            queuesize=100)
    return default_threadpool
