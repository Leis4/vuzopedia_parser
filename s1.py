def f(x, h):
    if (h == 3 or h == 5) and x <= 12:
        return True
    if h == 5 and x > 12:
        return False
    if x <= 12:
        return False
    else:
        if h % 2 == 0:
            return f(x - 3, h + 1) or f(x - 7, h + 1) or f(x // 5, h + 1)
        else:
            return f(x - 3, h + 1) and f(x - 7, h + 1) and f(x // 5, h + 1)

def f1(x, h):
    if h == 3 and x <= 12:
        return True
    if h == 3 and x > 12:
        return False
    if x <= 12:
        return False
    else:
        if h % 2 == 0:
            return f1(x - 3, h + 1) or f1(x - 7, h + 1) or f1(x // 5, h + 1)
        else:
            return f1(x - 3, h + 1) and f1(x - 7, h + 1) and f1(x // 5, h + 1)

for x in range(13, 1000):
    if f(x, 1):
        print(x)

#
# print("----------------------")

for x1 in range(13, 1000):
    if f1(x1, 1):
        print(x1)