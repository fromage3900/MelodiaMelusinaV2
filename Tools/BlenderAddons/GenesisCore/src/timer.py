import bpy
import traceback
from queue import Queue
from typing import Any


class Timer:
    TimerQueue = Queue()

    @classmethod
    def put(cls, delegate: Any):
        cls.TimerQueue.put(delegate)

    @classmethod
    def executor(cls, t):
        if type(t) in {list, tuple}:
            t[0](*t[1:])
        else:
            t()

    @classmethod
    def run(cls):
        return cls.run_ex(cls.TimerQueue)

    @classmethod
    def run_ex(cls, queue: Queue):
        while not queue.empty():
            t = queue.get()
            try:
                cls.executor(t)
            except Exception:
                traceback.print_exc()
            except KeyboardInterrupt:
                ...
        return 0.016666666666666666

    @classmethod
    def clear(cls):
        while not cls.TimerQueue.empty():
            cls.TimerQueue.get()

    @classmethod
    def wait_run(cls, func):
        def wrap(*args, **kwargs):
            q = Queue()

            def wrap_job(q):
                try:
                    res = func(*args, **kwargs)
                    q.put(res)
                except Exception as e:
                    q.put(e)

            cls.put((wrap_job, q))
            res = q.get()
            if isinstance(res, Exception):
                raise res
            return res

        return wrap

    @classmethod
    def wait_run_with_context(cls, func):
        def wrap(*args, **kwargs):
            q = Queue()

            def wrap_job(q):
                try:
                    override = bpy.context.copy()
                    override["area"] = [area for area in bpy.context.screen.areas if area.type == "VIEW_3D"][0]
                    with bpy.context.temp_override(**override):
                        res = func(*args, **kwargs)
                        q.put(res)
                except Exception as e:
                    q.put(e)

            cls.put((wrap_job, q))
            res = q.get()
            if isinstance(res, Exception):
                raise res
            return res

        return wrap

    @classmethod
    def reg(cls):
        bpy.app.timers.register(cls.run, persistent=True)

    @classmethod
    def unreg(cls):
        cls.clear()
        try:
            bpy.app.timers.unregister(cls.run)
        except Exception:
            ...


def register():
    Timer.reg()


def unregister():
    Timer.unreg()
