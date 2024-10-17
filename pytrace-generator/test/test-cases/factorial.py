def factorical(n):
    if n <= 1:
        return 1
    prev = factorical(n - 1)
    a = n * prev
    return a

res1 = factorical(2)
