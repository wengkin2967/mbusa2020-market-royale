import threading
import multiprocessing
import platform

TIME = 5   # seconds for one turn

class Timer():
    def call_timeout(timeout, func, args=(), kwargs={}):
        try:
            p = multiprocessing.Process(target=func, args=args, kwargs=kwargs)
            p.start()
            p.join(timeout)

            if p.is_alive():
                p.terminate()
                return False
            else:
                return True
        except Exception as e:
            print("Exceptional")
            raise e

    def timeout(func, args=(), kwargs={}, duration=TIME, default=None):
        '''This function will spwan a thread and run the given function using the args, kwargs and 
        return None if the duration is exceeded 
               an object of type Exception if result of Exception when running func.
               else result of func
        NOTE: thus will be confusing if func returns a string.
        ''' 
        if not callable(func):
            raise TypeError("{} not callable".format(func))

        if platform.system() == "Windows":
            return func(*args, **kwargs)

        try:
            if Timer.call_timeout(TIME, func, args, kwargs):
                return func(*args, **kwargs)
            else:
                return None 
        except Exception as e:
            raise e


from contextlib import contextmanager
import os,sys

@contextmanager
def silence_stdout():
    new_target = open(os.devnull, "w")
    old_target = sys.stdout
    sys.stdout = new_target
    try:
        yield new_target
    finally:
        sys.stdout = old_target
