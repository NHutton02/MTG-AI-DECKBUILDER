from math import comb

def hypergeom_successes(population, success_states, draws, k_or_more):
    total = 0
    for k in range(k_or_more, min(success_states, draws)+1):
        ways = comb(success_states, k) * comb(population - success_states, draws - k)
        total += ways
    denom = comb(population, draws)
    return total / denom if denom else 0.0
