import random


def weighted_choices(weighted_population, k):
    s = []
    for choice, weight in weighted_population:
        for i in range(weight):
            s.append(choice)
    results = []
    while s:
        r = random.choice(s)
        results.append(r)
        if len(results) == k:
            break
        s = [item for item in s if item != r]
    d = dict(weighted_population)
    return sorted(results, key=lambda x: d[x], reverse=True)
