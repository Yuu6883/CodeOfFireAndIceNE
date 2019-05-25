from ..nn_constants import CROSS_OVER_RATE, MUTATION_RANGE, MUTATION_RATE, SWAP_RATE
import random

def crossover(weight1, weight2):
    copy = weight1.copy()
    for index in range(len(weight1)):
        if random.random() < CROSS_OVER_RATE:
            copy[index] = weight2[index]
    return copy

def mutate(weights):
    copy = weights.copy()
    for index in range(len(copy)):
        if random.random() < MUTATION_RATE:
            copy[index] += (random.random() * 2 - 1) * MUTATION_RANGE
    return copy