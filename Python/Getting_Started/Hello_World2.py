#
# A "for" loop allows you to do things repeatedly.
# Strings are " " and can be assigned to a variable
# Python is very flexible in its use of strings.
#
hello = "Hello World, this is Python"
for i in range(20):
    outstr= " "*i + hello+" "+str(i)
    print(outstr)
# You can usually print anything.
nf = 1.2345678901234567890
print("Now I print the nf variable")
print(nf)
# If you want to print pretty, use format strings.
print("The value of nf is {0:2.3f}".format(nf))
# The range() function actually creates an "array" 
