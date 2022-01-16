from ylang.el import *
if __name__ == '__main__':
  print(funcall(Q.list, [1,2,['a', 'b', funcall(Q.cons, ['uu', 'zz'])], 3]).v)
  # (1 2 ('a' 'b' ('uu' . 'zz')) 3)