import math
from math import comb
import random

#h=hp of the unit dealing damage, p is prob threshold calculated from atk def and piercing, and x is the dmg qty we are asking the probability of
def dmg_byMath(h, p, x): #correct (at least quite close)
    n = 12 * h
    lo = 12 * x
    hi = 12 * x + 11
    return sum(comb(n, k) * p**k * (1-p)**(n-k) for k in range(lo, hi+1))

def dmg_bySim(h, p, x, s):

    dmgIsX = 0
    for _ in range(s):
        hits = 0
        for _ in range(h*12):
            if random.random() <= p:
                hits += 1
        if math.floor(hits/12) == x:
            dmgIsX += 1
    return dmgIsX/s

def avg_bySimple(h, p): #NOT CORRECT
    return h*p

def avg_bySim(h, p, s):
    dmg = 0
    if h>12: raise RuntimeError("H can't be larger than 12")
    for x in range(0, 13, 1): #1 to 12
        dmg += x*dmg_bySim(h, p, x, s)
    return dmg
    
def avg_byMath(h, p):
    dmg = 0
    if h>12: raise RuntimeError("H can't be larger than 12")
    for x in range(0, 13, 1): #1 to 12
        dmg += x*dmg_byMath(h, p, x)
    return dmg

# print(dmg_byMath(6, 0.7, 5))
# print(dmg_bySim(6, 0.7, 5))
print(avg_bySimple(6, 0.7))
print(avg_bySim(6, 0.7, 10000))
print(avg_byMath(6, 0.7))