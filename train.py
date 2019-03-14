from tetris import TetrisApp
from deap import base, creator, tools, algorithms
import numpy as np
from operator import attrgetter

# from deap import base
# from deap import creator
# from deap import tools

# creator.create("FitnessMax", base.Fitness, weights=(1.0,))
# creator.create("Individual", list, fitness=creator.FitnessMax)

# IND_SIZE=10

# toolbox = base.Toolbox()
# toolbox.register("attr_float", random.random)
# toolbox.register("individual", tools.initRepeat, creator.Individual,
#                  toolbox.attr_float, n=IND_SIZE)

# creator.create("Individual", array.array, typecode="d", fitness=creator.FitnessMax)
# creator.create("Individual", numpy.ndarray, fitness=creator.FitnessMax)

# toolbox.register("mutate", tools.mutGaussian, mu = 0, sigma = sigma, indpb=1.0)
# The greater the tournament size, the greater the selection pressure
# toolbox.register("select", tools.selTournament, tournsize=5)  

# VARIATIONS

# for g in range(NGEN):
#     # Select and clone the next generation individuals
#     offspring = map(toolbox.clone, toolbox.select(pop, len(pop)))

#     # Apply crossover and mutation on the offspring
#     offspring = algorithms.varAnd(offspring, toolbox, CXPB, MUTPB)

#     # Evaluate the individuals with an invalid fitness
#     invalid_ind = [ind for ind in offspring if not ind.fitness.valid]
#     fitnesses = toolbox.map(toolbox.evaluate, invalid_ind)
#     for ind, fit in zip(invalid_ind, fitnesses):
#         ind.fitness.values = fit

#     # The population is entirely replaced by the offspring
#     pop[:] = offspring


if __name__ == "__main__":
    creator.create("FitnessMax", base.Fitness, weights=(1.0,))
    creator.create("Individual", list, fitness=creator.FitnessMax)

    toolbox = base.Toolbox()

    def random_between(lo, hi):
        return np.random.random() * (hi - lo) + lo

    toolbox.register("weight", random_between, -1, 1)
    toolbox.register("individual", tools.initRepeat, creator.Individual, toolbox.weight, n=5)
    toolbox.register("population", tools.initRepeat, list, toolbox.individual)
    toolbox.register("mate", tools.cxBlend, alpha=0.4)
    toolbox.register("mutate", tools.mutGaussian, mu=0.0, sigma=0.3, indpb=0.05)
    toolbox.register("select", tools.selTournament, tournsize=5)

    #------------------------------------------------------------
    # Define Parameters
    # Setup to grab statistics
    #   - Max, mean, min, std, variance
    # Setup containers for highest score and highest scoring individual
    # Create a Genetic Algorithm loop
    #   - This loop will achieve the following:
    #       a. Select and clone the next generation individuals
    #       b. Apply crossover and mutation on the offspring
    #       c. Replace population with offspring
    #------------------------------------------------------------
    n_gen = 50
    # n_gen = 100
    prob_xover = 0.3
    prob_mut = 0.05
    pop = toolbox.population(n=25)
    # pop = toolbox.population(n=1000)
    game = TetrisApp(training=True)
    best_ind = []
    best_score = -1

    max_out  = open("max50.txt", "w")
    mean_out = open("mean50.txt", "w")
    min_out  = open("min50.txt", "w")
    std_out  = open("std50.txt", "w")
    var_out  = open("var50.txt", "w")

    for g in range(1, n_gen + 1):
        print("Current Generation " + str(g))
        scores = []
        for ind in pop:
            score = game.run_train(ind)
            scores.append(score)
            ind.fitness.values = (score,)
            if score > best_score:
                best_ind = ind
                best_score = score

        max_out.write(str(max(scores)) + "\n")
        mean_out.write(str(np.mean(scores)) + "\n")
        min_out.write(str(min(scores)) + "\n")
        std_out.write(str(np.std(scores)) + "\n")
        var_out.write(str(np.var(scores)) + "\n")

        offspring = map(toolbox.clone, toolbox.select(pop, len(pop)))
        offspring = algorithms.varAnd(offspring, toolbox, prob_xover, prob_mut)
        pop[:] = offspring

    max_out.close()
    mean_out.close()
    min_out.close()
    std_out.close()

    print("Top Score:" + str(best_score))
    file = open("best_weights50.txt", "w")
    file.write(str(best_ind))
    file.close()