import re as _re
from ctypes import c_ulonglong as _ULL
from ctypes import c_longlong as _LL
from ctypes import c_long as _L
from enum import IntEnum as _IntEnum
from dataclasses import dataclass as _dataclass
from weakref import WeakKeyDictionary as _WeakKeyDict
import typing as _t

#define ULLONG_MAX      0xffffffffffffffffULL   /* max unsigned long long */
#define LLONG_MAX       0x7fffffffffffffffLL    /* max signed long long */
#define LLONG_MIN       (-0x7fffffffffffffffLL-1) /* min signed long long */

def LL(x): return _LL(x).value
def ULL(x): return _ULL(x).value

INTPTR_MAX = LL(9223372036854775807)
INTPTR_MIN = LL(-INTPTR_MAX-1)

ULLONG_MAX = ULL(0xffffffffffffffff)
LLONG_MAX = LL(0x7fffffffffffffff)
LLONG_MIN = LL(-0x7fffffffffffffff - 1)
LLONG_WIDTH = 64
ULLONG_WIDTH = 64

GCTYPEBITS = 3
"""Number of bits in a Lisp_Object tag."""

def EMACS_INT(x): return LL(x)
def EMACS_UINT(x): return ULL(x)
EMACS_INT_MAX = LLONG_MAX
EMACS_INT_WIDTH = LLONG_WIDTH
EMACS_UINT_WIDTH = ULLONG_WIDTH

class Lisp_Bits(_IntEnum):
  VALBITS = EMACS_INT_WIDTH - GCTYPEBITS
  FIXNUM_BITS = VALBITS + 1

VALBITS = Lisp_Bits.VALBITS
"""Number of bits in a Lisp_Object value, not counting the tag."""
FIXNUM_BITS = Lisp_Bits.FIXNUM_BITS
"""Number of bits in a fixnum value, not counting the tag."""

INTTYPEBITS = (GCTYPEBITS - 1)
"""Number of bits in a fixnum tag; can be used in #if."""

VAL_MAX = (EMACS_INT_MAX >> (GCTYPEBITS - 1))
"""The maximum value that can be stored in a EMACS_INT, assuming all
bits other than the type bits contribute to a nonnegative signed value.
This can be used in #if, e.g., '#if USE_LSB_TAG' below expands to an
expression involving VAL_MAX."""

USE_LSB_TAG = (VAL_MAX // 2) < INTPTR_MAX
"""Whether the least-significant bits of an EMACS_INT contain the tag.
On hosts where pointers-as-ints do not exceed VAL_MAX / 2, USE_LSB_TAG is:
 a. unnecessary, because the top bits of an EMACS_INT are unused, and
 b. slower, because it typically requires extra masking.
So, USE_LSB_TAG is true only on hosts where it might be useful."""

VALMASK = EMACS_UINT(-(1 << GCTYPEBITS)) if USE_LSB_TAG else VAL_MAX
"""Mask for the value (as opposed to the type bits) of a Lisp object."""

_WS = _re.compile(r'\s')
_BADSYM = _re.compile(r'\s|[|]')


def EQ(a, b): return a is b
def NILP(x): return EQ(x, Qnil)
def NO(x): return NILP(x) or EQ(x, Qf)
def SYMBOLP(x): return isinstance(x, Symbol)
def CONSP(x): return isinstance(x, Lisp_Cons)

class Lisp_Object:
  pass

@_dataclass
class Lisp_Cons(Lisp_Object):
  car: Lisp_Object
  cdr: Lisp_Object

  def repr(self):
    if NILP(self.cdr):
      return f"({self.car!r})"
    elif CONSP(self.cdr):
      return f"({self.car!r} {repr(self.cdr)[1:-1]})"
    else:
      return f"({self.car!r} . {self.cdr!r})"

  __repr__ = repr

class Symbol(str, Lisp_Object):
  def __repr__(self):
    s = str(self)
    if _BADSYM.search(s):
      return "|" + s.replace("|", "\\|") + "|"
    else:
      return s

  def __bool__(self):
    return not NO(self)

  @classmethod
  def intern(cls, name: str, ob=None):
    if ob is None:
      ob = obarray
    try:
      return ob[ob.index(name)]
    except ValueError:
      sym = Symbol(name)
      ob.append(sym)
      return sym

  @classmethod
  def intern_soft(cls, name: str, ob=None):
    if ob is None:
      ob = obarray
    try:
      return ob[ob.index(name)]
    except ValueError:
      return Qnil

Qnil, Qt, Qf = obarray = [
  Symbol("nil"),
  Symbol("t"),
  Symbol("f"),
]

class Q_:
  def __class_getitem__(cls, item) -> Symbol:
    return cls.get(item)
  def __getitem__(self, item) -> Symbol:
    return self.__class__.get(item)
  def __getattr__(self, item) -> Symbol:
    return self.__class__.getattr(item)
  @classmethod
  def compile(cls, item):
    if SYMBOLP(item):
      return item
    return item.replace('_', '-')
  @classmethod
  def get(cls, item) -> Symbol:
    if SYMBOLP(item):
      return item
    return Symbol.intern(item)
  @classmethod
  def getattr(cls, item) -> Symbol:
    if SYMBOLP(item):
      return item
    return cls.get(cls.compile(item))


class SymbolDict(_WeakKeyDict):
  def __init__(self, tag):
    object.__setattr__(self, '_tag', tag)
    object.__setattr__(self, '_init', True)
    super().__init__()
    object.__setattr__(self, '_init', False)
  def __getitem__(self, item):
    return self.get(Q.get(item), Qnil)
  def __setitem__(self, key, value):
    return super().__setitem__(Q.get(key), value)
  def __getattr__(self, key):
    if object.__getattribute__(self, '_init'):
      return super().__getattribute__(key)
    else:
      key = Q.getattr(key)
      return self.get(key, Qnil)
  def __setattr__(self, key, value):
    if object.__getattribute__(self, '_init'):
      return super().__setattr__(key, value)
    else:
      self[Q.getattr(key)] = value
  def __call__(self, value=None, *, name=None):
    def setter(name, value):
      self[Q.getattr(name)] = value
      return value
    if name is None:
      return setter(value.__name__, value)
    else:
      return _partial(setter, name)


Q = Q_()
V = SymbolDict("V")
F = SymbolDict("F")
S = SymbolDict("S")

V.nil = None
V.t = True
V.f = False

@_dataclass
class Lisp_Subr(Lisp_Object):
  symbol_name: str
  function: _t.Callable
  min_args: int
  max_args: int

class maxargs(_IntEnum):
  MANY = -2
  UNEVALLED = -1

MANY = maxargs.MANY
UNEVALLED = maxargs.UNEVALLED

def DEFUN(lname, minargs, maxargs):
  def definer(f):
    S[lname] = Lisp_Subr(lname, f, minargs, maxargs)
    F[lname] = f
    return f
  return definer

