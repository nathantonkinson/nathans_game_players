#handles errors
#mostly can turn off/on warnings

import warnings
import os
import sys


PRINT_WARNINGS = False #this can be turned on with errorHandler.PRINT_WARNINGS = True
PRINT_INFORMATION = True #debug stuff. Though honestly, I will turn off/on various parts because I usually always want some printing

#these should not stop execution
def warning(msg: str):
    if PRINT_WARNINGS:
        print(f"Warning {msg}")
        # warnings.warn(msg, RuntimeError) #could use different kinds of errors

#these stop execution
#maybe somehow we can automatically grab context? idk
def error(msg: str):
    # raise RuntimeError(msg)
    print(f"Error: {msg}")
    # os._exit(1) #this is a nuclear option that bypasses even try/finally blocks
    sys.exit(1) #I don't think the 1 matters
    # raise SystemExit("some optional message here") #does the same thing as sys.exit

def info(msg: str):
    if PRINT_INFORMATION:
        print(f"{msg}")