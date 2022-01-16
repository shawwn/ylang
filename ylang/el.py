from ylang.emacs import *
from functools import singledispatch as _singledispatch
from functools import wraps as _wraps
from functools import partial as _partial
from functools import lru_cache as _cache
from inspect import unwrap as _unwrap

class View:
  def __init__(self, l, *slices):
    self.l = l
    self._slices = slices

  def seq(self):
    l = self.l
    for s in self._slices:
      l = l[s]
    return l

  def __len__(self): return len(self.seq())
  def __str__(self): return str(self.seq())
  def __repr__(self): return repr(self.seq())

  def __getitem__(self, item):
    if isinstance(item, slice):
      return self.__class__(self.l, *self._slices, item)
    elif isinstance(item, tuple):
      return self.__class__(self.l, *self._slices, *item)
    else:
      return self.seq()[item]

@F
@_singledispatch
def symbolp(x):
  return isinstance(x, Symbol)

@F
@_singledispatch
def listp(x):
  return isinstance(x, list)

@listp.register
def _(x: View):
  return isinstance(x, View)

@F
@_singledispatch
def hash_table_p(x):
  return isinstance(x, dict)

@DEFUN("null", 1, 1)
def null(x):
  return (x is Qnil) or (listp(x) and (len(x) <= 0))

@DEFUN("eq", 2, 2)
def eq(a, b):
  return (a is b) or (null(a) and null(b))

@DEFUN("eqv", 2, 2)
def eqv(a, b):
  return (a == b) or (null(a) and null(b))

@DEFUN("make-symbol", 1, 1)
def make_symbol(name: str):
  return Symbol(name)

@DEFUN("symbol-name", 1, 1)
def symbol_name(sym: Symbol):
  return str(sym)

@DEFUN("intern", 1, 2)
def intern(name: str, obarray=obarray):
  return Symbol.intern(name, obarray)

@DEFUN("intern-soft", 1, 2)
def intern_soft(name: str, obarray=obarray):
  return Symbol.intern_soft(name, obarray)

@DEFUN("mapatoms", 1, 2)
def mapatoms(function, obarray=obarray):
  for sym in obarray:
    function(sym)

@DEFUN("unintern", 1, 2)
def unintern(symbol, obarray=obarray):
  try:
    del obarray[obarray.index(symbol)]
    return Qt
  except ValueError:
    return Qnil

@DEFUN("keywordp", 1, 1)
def keywordp(x):
  return symbolp(x) and symbol_name(x).startswith(":")

@DEFUN("car", 1, 1)
def car(x): return x[0] if len(x) > 0 else Qnil

@DEFUN("cdr", 1, 1)
def cdr(x): return x[1:]

@DEFUN("cadr", 1, 1)
def cadr(x): return car(cdr(x))

@DEFUN("cddr", 1, 1)
def cddr(x): return cdr(cdr(x))

@DEFUN("cdar", 1, 1)
def cdar(x): return cdr(car(x))

@DEFUN("gethash", 2, 2)
def gethash(k, h):
  return h[k]

@DEFUN("elt", 2, 2)
def elt(h, k):
  return h[k]

class emacs_env:
  def intern(self, name: str):
    return Symbol.intern(name)
  def make_string(self, value: str):
    return EmacsValue.wrap(value)
  def make_integer(self, value: int):
    return EmacsValue.wrap(value)
  def make_float(self, value: float):
    return EmacsValue.wrap(value)

@_cache
def get_env():
  return emacs_env()

def sym(name: str):
  return get_env().intern(name)

def unwrap(obj):
  if obj is None:
    obj = sym("nil")
  elif obj is False:
    obj = sym("f")
  elif obj is True:
    obj = sym("t")
  elif isinstance(obj, str):
    obj = string(obj)
  elif isinstance(obj, int):
    obj = make_int(obj)
  elif isinstance(obj, float):
    obj = make_float(obj)
  elif isinstance(obj, list):
    obj = funcall(Q.list, obj)

  if isinstance(obj, EmacsValue):
    return obj.v
  else:
    raise TypeError("cannot convert %s to emacs value" % type(obj))

def string(x):
  return get_env().make_string(x)

def make_int(x):
  return get_env().make_integer(x)

def make_float(x):
  return get_env().make_float(x)

class EmacsValue:
  def __init__(self, v):
    self.v = v

  @classmethod
  def wrap(cls, v):
    return cls(v)



def funcall(f, args):
  args = list(args)
  for i in range(len(args)):
    args[i] = unwrap(args[i])
  f_val = unwrap(f)
  result = F[f_val](*args)
  return EmacsValue.wrap(result)
