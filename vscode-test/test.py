from wypp import *

@record
class Item:
    name: str

item1 = Item('foo')
item2 = Item('bar')

@record
class Items:
    items: list[Item]

invoices = []

for i in range(1000):
    x = Item(str(i))
    y = Items([item1, item2, x])
    invoices.append(y)

print(invoices[3])
