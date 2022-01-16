from ylang.emacs.lisp import *

@DEFUN("cons", 2, 2)
def Fcons(car: Lisp_Object, cdr: Lisp_Object):
  return Lisp_Cons(car, cdr)

@DEFUN("list", 0, MANY)
def Flist(*args: Lisp_Object):
  nargs = len(args)
  val = Qnil
  while nargs > 0:
    nargs -= 1
    val = Fcons(args[nargs], val)
  return val
