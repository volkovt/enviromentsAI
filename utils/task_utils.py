def calcular_xp_por_bcp(bcp):
    return 10 + next((i for i, f in enumerate(_fib_gen(bcp)) if f == bcp), 0)

def _fib_gen(limit):
    a, b = 0, 1
    while a <= limit:
        yield a
        a, b = b, a + b
