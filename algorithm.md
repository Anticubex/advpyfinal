Teo 2025

The datatypes and flow until **The Algorithm** are self-explanatory

When we reach the start, we'll have:

1. An enumerated set of items that exist
2. A set of input items (materials) and target items (products)
3. A set of processes that convert between different materials, at limited rates

First, we construct a hypergraph representing item flow:

- Each vertex is an item type.
- Each edge is a process

We can verify that the factory can in fact produce the inputs from the outputs by pathfinding through the
hypergraph (this pathfinding is the greedy algorithm, as it greedily traverses the next available edge to
maximize the visited nodes).

We have the limitation that each process must adhere to ratios---luckily, those ratios are linear,
and thus can be represented with a linear system of equations: each equation/row represents an item balance
given the production ratios, with the variable vector representing the production ratios.
We can do this by encoding the throughput of each processes' as the coeffecients of the matrix
However, this can't be directly solved: We need to find the maximal constrained ratio, which naive solving can't do.

Instead, we use scipy's linear programming to find the optimal production ratios.

We set up the system as a group of constraints, using that net item matrix.
