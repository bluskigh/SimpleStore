from functools import wraps
from flask import request, redirect, session, flash

def logged_in(func):
    @wraps(func)
    def wrapper_(*args, **kwargs):
        if session.get('userid') is None:
            flash('You\'re not signed in for that action. Attempt signing in.', 'info') 
            return redirect('/signin')
        # is signed in
        return func(*args, **kwargs)
    return wrapper_

def redirect_logged_in(func):
    @wraps(func)
    def wrapper_(*args, **kwargs):
        if session.get('userid') is not None:
            flash('The current action you\'re trying to do is not accessible when logged in.', 'info')
            return redirect('/')
        # is not logged in, allow to sign up / sign in 
        return func(*args, **kwargs)
    return wrapper_
