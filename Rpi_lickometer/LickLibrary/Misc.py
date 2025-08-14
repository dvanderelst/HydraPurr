import pickle
from collections.abc import Iterable  # drop `.abc` with Python 2.7 or lower


class blinker:
    def __init__(self, values='-+'):
        self.length = len(values)
        self.index = 0
        self.values = values

    def tick(self):
        self.index = self.index + 1
        if self.index == self.length: self.index = 0

    def get_value(self):
        value = self.values[self.index]
        self.tick()
        return value



def lst2line(lst):
    txt = ''
    for i in lst: txt = txt + str(i) + ','
    txt = txt.rstrip(',')
    return txt


def isList(obj):
    return isinstance(obj, list)


def iterable(obj):
    return isinstance(obj, Iterable)


def list2text(lst, sep=' '):
    if type(lst) == str: return lst
    text = ''
    for x in lst:
        if type(x) == float: x = '%.2f' % x
        text = text + sep + str(x)
    text = text.rstrip(sep)
    text = text.lstrip(sep)
    return text


def pickle_save(file, object):
    f = open(file, 'wb')
    pickle.dump(object, f)
    f.close()


def pickle_load(file):
    f = open(file, 'rb')
    object = pickle.load(f)
    f.close()
    return object


class Counter:
    def __init__(self, max, value=0):
        self.max = max
        self.value = value

    def increase(self, n=1):
        self.value = self.value + n
        if self.value > self.max: self.value = 0


def even(x):
    if x % 2 == 0: return True
    return False


def fields2str(fields, blank=False):
    result = ''
    if not blank:
        for x in fields: result += str(x) + ','
    if blank:
        for x in fields: result += '?' + ','
    result = result.rstrip(',')
    result = '(' + result + ')'
    return result
