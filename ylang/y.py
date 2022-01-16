from ylang.el import *
from contextlib import contextmanager

def y_eq(a, b):
  return a is b

def y_is(a, b):
  return a == b

def y_next(h):
  if keywordp(car(h)):
    return cddr(h)
  else:
    return cdr(h)

def y_key(x):
  if keywordp(x):
    return intern(symbol_name(x)[1:])
  else:
    return x

def y_for(h):
  i = -1
  while h:
    if keywordp(car(h)):
      k = y_key(car(h))
    else:
      i += 1
      k = i
    if keywordp(car(h)):
      v = cadr(h)
    else:
      v = car(h)
    yield k, v
    if keywordp(car(h)):
      h = cddr(h)
    else:
      h = cdr(h)

def y_get(h, k, *, cmp=y_eq):
  if hash_table_p(h):
    return gethash(k, h)
  elif listp(h):
    for key, val in y_for(h):
      if cmp(key, k):
        return val
  else:
    return elt(h, k)

def y_put(h, k, *args):
  v = car(args)
  wipe = null(args)
