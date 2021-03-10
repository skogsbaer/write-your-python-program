spam = "global spam"
def local_test():
   def do_local():
       spam = "local spam"
   def do_nonlocal():
       nonlocal spam
       spam = "nonlocal spam"
   def do_global():
       global spam
       print('spam in do_global: ' + str(id(spam)))
       spam = "IT WORKS"
   spam = "my precious"
   do_local()
   print(spam)

   do_nonlocal()
   print(spam)

   do_global()
   print(spam)

print('spam at toplevel: ' + str(id(spam)))
