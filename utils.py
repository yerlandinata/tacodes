from functools import reduce

pipe = lambda *args: lambda x: reduce(lambda acc, f: f(acc), args, x)
