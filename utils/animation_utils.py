import sys
import threading
import time
import inspect
from typing import Callable
from functools import wraps


def loading_animation(message_func: Callable[[], str], stop_event: threading.Event, resume_event: threading.Event):
    """
    Display a loading animation while waiting for an event to be set.
    
    Args:
        message_func: A function that returns the message to display.
        stop_event: An event to stop the animation.
        resume_event: An event to pause the animation.

    """
    spinner = ['|', '/', '-', '\\']
    spinner_index = 0
    while not stop_event.is_set():
        message = message_func()
        sys.stdout.write(f"\r{message} {spinner[spinner_index]}")
        sys.stdout.flush()
        spinner_index = (spinner_index + 1) % len(spinner)
        time.sleep(0.1)
        resume_event.wait()
    sys.stdout.write("\r" + " " * (len(message_func()) + 2) + "\r")
    sys.stdout.flush()

def with_loading_animation(message_func: Callable[[], str]):
    """
    Decorator to display a loading animation while executing a function.

    Args:
        message_func: A function that returns the message to display.

    Returns:
        Callable: The decorated function.
    
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Inspect the function's signature
            sig = inspect.signature(func)
            parameters = sig.parameters
            if 'stop_event' in parameters:
                stop_event = kwargs.get('stop_event')
            else:
                stop_event = threading.Event()
            if 'resume_event' in parameters:
                resume_event = kwargs.get('resume_event')
            else:
                resume_event = threading.Event()
                resume_event.set()
            animation_thread = threading.Thread(
                target=loading_animation, 
                args=(message_func, stop_event, resume_event), 
                daemon=True
            )
            animation_thread.start()
            try:
                return func(*args, **kwargs)
            finally:
                stop_event.set()
                resume_event.set()
                animation_thread.join()
        return wrapper
    return decorator