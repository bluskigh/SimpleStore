def decorater(func):
    def funcSomething():
        print("This will run before calling func")
        func()
        print("this will run after calling func")
    return funcSomething 

def something():
    print("something")
print(decorater(something))
