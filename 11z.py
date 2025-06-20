def moves(heap):
    return heap -3, heap - 7, heap//5

def game_over(pos):
    return pos <= 12

def win1(pos):
    return not game_over(pos) and any(game_over(m) for m in moves(pos))

def lose1(pos):
    return all(win1(m) for m in moves(pos))

def lose1_bad (pos):
    return any(win1(m) for m in moves(pos))

def win2(pos):
    return not win1(pos) and any(lose1(m) for m in moves(pos))

def lose2(pos):
    return all(win1(m) or win2(m) for m in moves(pos)) \
            and any(win2(m) for m in moves(pos))

z19 = [S for S in range(13, 1000) if lose1_bad(S)]
z20 = [S for S in range(13, 1000) if win2(S)]
z21 = [S for S in range(13, 1000) if lose2(S)]

print(max(z19))
print(*z20)
print(max(z21))