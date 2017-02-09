'''
collection of isinstance funcs
'''

from types import ModuleType, FunctionType, GeneratorType

def isstr(obj):
    '''
    isstr
    '''
    return isinstance(obj, str)

def isunicode(obj):
    '''
    isunicode
    '''
    return isinstance(obj, unicode)

def isint(obj):
    '''
    isint
    '''
    return isinstance(obj, int)

def islong(obj):
    '''
    islong
    '''
    return isinstance(obj, long)

def isfloat(obj):
    '''
    isfloat
    '''
    return isinstance(obj, float)

def ismodule(obj):
    '''
    ismodule
    '''
    return isinstance(obj, ModuleType)

def isfunction(obj):
    '''
    isfunction
    '''
    return isinstance(obj, FunctionType)

def isgenerator(obj):
    '''
    isgenerator
    '''
    return isinstance(obj, GeneratorType)

def isscalar(obj):
    '''
    isscalar
    '''
    return  obj is None or \
            isstr(obj) or \
            isunicode(obj) or \
            isint(obj) or \
            islong(obj) or \
            isfloat(obj)

def islist(obj):
    '''
    islist
    '''
    return isinstance(obj, list)

def isdict(obj):
    '''
    isdict
    '''
    return isinstance(obj, dict)

def isa(obj, *types, is_all=False):
    if is_all:
        return all([isinstance(obj, t) for t in types])
    return any([isinstance(obj, t) for t in types])
