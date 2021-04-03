from functools import wraps
def dec(func):
    @wraps(func)
    def wrapper_(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper_ 

@dec
def doSomething():
    print("I am doing something right now")

print(doSomething())

@dec
def paramSomething(first, second):
    first += ' added to first'
    second += ' added to second'
    return first + second 

# question, what happens when we pass in params to the function when using a decorator function?
# answer, the params are not passed, and you will git the wrong return

print(paramSomething("thing", "other thing"))

import time
def timer(func):
    @wraps(func)
    def wrapper_(*args, **kwargs):
        start_time = time.perf_counter()
        func(*args, **kwargs)
        end_time = time.perf_counter()
        runtime = end_time - start_time
        print(f'Ran function {func.__name__} in {runtime:.4f} secs')
    return wrapper_

@timer
def waste_some_time(num_times):
    for _ in range(num_times):
        sum([i**2 for i in range(10000)])

waste_some_time(1)
