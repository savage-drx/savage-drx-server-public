# -------------------------------------------------------------------------------------------------------
#          Name: sh_executor.py
#   Description: Thread Pool Executor for task
# -------------------------------------------------------------------------------------------------------


import concurrent.futures
import datetime
from typing import Optional
import inspect


class ExecutorContext:
    THREAD_POOL_EXECUTOR = Optional[concurrent.futures.ThreadPoolExecutor]
    MIN_THREAD_WORKERS = 100

    @staticmethod
    def init():
        ExecutorContext.THREAD_POOL_EXECUTOR = concurrent.futures.ThreadPoolExecutor(
            max_workers=ExecutorContext.MIN_THREAD_WORKERS)

        # log should be after the start of the thread since it uses sh_executor
        d = datetime.datetime.now()
        date_template = d.strftime("%Y.%m.%d - %H:%M:%S")
        print(f'[INFO]  [{date_template}]   Initializing Thread Pool Executor...')


# Usage example:
#
# def task(msg1, msg2):
#     pass
#
# submit_task(task, "a", "b")
#
def submit_task(task, *args, **kwargs):
    try:
        # Returns a Future object with api:
        #
        # future.cancel()
        # future.cancelled()
        # future.running()
        # future.done()
        # future.result() <-- this is the blocking
        # future.exception(timeout=None)
        # future.add_done_callback(fn)
        # future.set_running_or_notify_cancel()
        # future.set_result(result)
        # future.set_exception(exception)
        return ExecutorContext.THREAD_POOL_EXECUTOR.submit(task, *args, **kwargs)
    except Exception as e:
        print(e)


def stop():
    ExecutorContext.THREAD_POOL_EXECUTOR.shutdown()


# Decorator
def threaded(task):
    def wrapper(*args, **kwargs):
        try:
            return ExecutorContext.THREAD_POOL_EXECUTOR.submit(task, *args, **kwargs)
        except Exception as e:
            print(e)
    wrapper.__signature__ = inspect.signature(task)
    return wrapper


# Decorator
def threaded_with_callback(callback, *threaded_args, **threaded_kwargs):
    def middle(task):
        def wrapper(*args, **kwargs):
            def wrapper_callback(future):
                if callback is not None:
                    callback(*threaded_args, **threaded_kwargs)
            try:
                result = ExecutorContext.THREAD_POOL_EXECUTOR.submit(task, *args, **kwargs)
                result.add_done_callback(wrapper_callback)
                return result
            except Exception as e:
                print(e)
        wrapper.__signature__ = inspect.signature(task)
        return wrapper
    return middle
