"""simulator.py
Implements the factory solver
Teo Fontana 2025, CIST 5B
"""

from typing import Dict, List, Set, Tuple
from itertools import chain
import numpy as np
from scipy.optimize import linprog, OptimizeResult

# Items are represented in a dict of name:quantity
Items = Dict[str, float]
EnumProc = Tuple[Dict[int, float], Dict[int, float]]

# A hypegraph edge
Edge = Tuple[Set[int], Set[int]]


class Process:
    """A type holding the data for a certain process"""

    def __init__(
        self,
        name: str,
        inputs: Items,
        outputs: Items,
        quantity: float,
        time_per_op: float,
    ):
        """Creates a new Process type

        Args:
            name (str): Name of process
            inputs (Items): What items and how many are taken in per operation
            outputs (Items): What and how many items are produced per operation
            quantity (int): How many of this process can run in parallel (i.e. amount of machines)
            time_per_op (float): How long does this process take per operation
        """
        self.name = name
        self.inputs = inputs
        self.outputs = outputs
        self.quantity = quantity
        self.time_per_op = time_per_op

    def extract_process_items(self):
        """Gets the unique names of items in the process"""
        return (self.inputs | self.outputs).keys()

    def convert_enumerated(
        self, item_to_enum: Dict[str, int], throughput: bool = True
    ) -> EnumProc:
        """
        Returns a tuple representing the process with item enumerations instead of names.
        If throughput is True, the values are throughput instead of per-operation
        """
        # The tuple is organized like so:
        scalar = 1.0 / self.time_per_op if throughput else 1.0
        return (
            {item_to_enum[name]: (amnt * scalar) for name, amnt in self.inputs.items()},
            {
                item_to_enum[name]: (amnt * scalar)
                for name, amnt in self.outputs.items()
            },
        )


class Factory:
    """A factory that coalesces a bunch of processes"""

    def __init__(
        self,
        materials: List[str],
        products: Items,
        processes: List[Process],
    ):
        """Creates a new factory

        Args:
            materials (List[str]): Materials the factory can take in
            products (Items): Products targeted to be made, in the target ratios
        """
        self.materials = materials
        self.products = products
        self.processes = processes

        # For enumeration later
        self.item_names: Set[str] = None
        self.item_to_enum: Dict[str, int] = None
        self.enum_to_item: Dict[int, str] = None

        self.hypergraph_edges: Set[Edge] = None

    def calculate(self):
        """Calculates the factory (basically does everything)"""

        self.enumerate_items_and_process()
        self.construct_hypergraph()
        if not self.check_path_to_targets():
            print("Factory cannot produce output products! The graph is untraversable!")
            return
        net_item_matrix = self.generate_net_matrix()
        result = self.solve_system(net_item_matrix)
        self.analyze_results(result, net_item_matrix)

    def enumerate_items_and_process(self):
        """Enumerates the items to prepare for hypergraph and matrix construction."""
        # Creates a set of item names among the members
        item_names = set()
        item_names |= set(self.materials)
        item_names |= self.products.keys()
        for process in self.processes:
            item_names |= process.extract_process_items()
        # The enumeration is a double dict
        self.item_names = item_names
        self.item_to_enum = {}
        self.enum_to_item = {}
        for idx, name in enumerate(item_names):
            self.item_to_enum[name] = idx
            self.enum_to_item[idx] = name

    def construct_hypergraph(self):
        """Constructs a hypergraph using the thingies"""
        # Hypergraph is represented by the mathematical set definition (see wikipedia)
        # X is names, this just defines E

        self.hypergraph_edges = set()
        for process in self.processes:
            tail = frozenset(self.item_to_enum[item] for item in process.inputs)
            head = frozenset(self.item_to_enum[item] for item in process.outputs)
            self.hypergraph_edges.add((tail, head))

    def check_path_to_targets(self) -> bool:
        """Checks the hypergraph to see if the machines can make the product"""
        # This is a hypergraph generalization of Dijkstra's algorithm, without keeping track
        # of the paths
        # (this explanation makes more sense when you note that vertices/nodes correspond to items)
        # It holds a visited/unvisited set for nodes and edges, seperately
        # It needs to make sure all the items that are outputs are visited at some point
        # when traversal begins with the input items in the frontier for free
        # an edge can be traversed when all it's tails are either in the frontier or visited
        # If all the output nodes are in the visited, we can terminate with a success
        # None of the edges are possible to traverse, then we've dead-ended

        untraversed_edges: Set[Edge] = set(self.hypergraph_edges)
        # A Cache of edges we can traverse at any moment
        frontier_edges: Set[Edge] = set()
        traversed_edges: Set[Edge] = set()

        unvisited_nodes: Set[int] = set()
        visited_nodes: Set[int] = set()
        targets: Set[int] = set()
        for i, item in enumerate(self.item_names):
            if item in self.materials:
                visited_nodes.add(i)
                continue
            if item in self.products.keys():
                targets.add(i)
            unvisited_nodes.add(i)

        def update_frontier():
            """Updates the frontier with new visited edges"""
            nonlocal untraversed_edges, frontier_edges
            new_edges: Set[Edge] = set()
            for edge in untraversed_edges:
                tail, _ = edge
                if not tail.issubset(visited_nodes):
                    continue
                new_edges.add(edge)
            if new_edges:
                frontier_edges.update(new_edges)
                untraversed_edges.difference_update(new_edges)
            return bool(new_edges)

        def traverse_edge(edge: Edge):
            """Traverses an edge on the frontier"""
            _, head = edge
            visited_nodes.update(head)
            unvisited_nodes.difference_update(head)

            traversed_edges.add(edge)

        while True:
            if frontier_edges:
                # TODO Possible improvement: some heuristic here in picking the edge
                edge_to_do = frontier_edges.pop()
                traverse_edge(edge_to_do)
                # Check if objectives reached
                if targets.issubset(visited_nodes):
                    return True
                continue
            elif untraversed_edges:
                if update_frontier():
                    continue
            break

        return False

    def generate_net_matrix(self) -> np.ndarray:
        """
        Generates a utility matrix that represents the
        net item amounts from a given production ratio
        where K * r = i, where K is the net matrix,
        r is the production ratios vector, and i is the item
        balances.
        """

        processes: List[EnumProc] = [
            process.convert_enumerated(self.item_to_enum, throughput=True)
            for process in self.processes
        ]

        net_item_matrix = np.zeros((len(self.item_names), len(self.processes)))
        for j, process in enumerate(processes):
            inputs, outputs = process
            for i, amnt in inputs.items():
                net_item_matrix[i, j] -= amnt
            for i, amnt in outputs.items():
                net_item_matrix[i, j] += amnt
        return net_item_matrix

    def solve_system(self, net_item_matrix: np.ndarray) -> OptimizeResult:
        """Solves the system with scipy"""
        # First, we precompute some values
        num_items: int = len(self.item_names)

        # These are items that are base materials or end products
        target_items = [
            self.item_to_enum[item] for item in chain(self.materials, self.products)
        ]
        # And vice versa; these have to be balanced
        balanced_items = [i for i in range(num_items) if i not in target_items]

        # c @ x should reflect how close it is to the target ratios
        # We evaluate this with the dot product's inverse, -(ratios * (K * x)) => c := -ratios * K
        target_ratios = np.zeros(num_items)
        for item, amount in self.products.items():
            target_ratios[self.item_to_enum[item]] = amount
        c = -target_ratios @ net_item_matrix

        # The inequality limitations are that the inputs and outputs have to be positive
        # row @ K @ x = row @ items < 0
        row_shape = (1, net_item_matrix.shape[0])
        io_constraints = []
        for item in self.materials:
            num = self.item_to_enum[item]
            row = np.zeros(row_shape)
            row[0, num] = 1
            row = row @ net_item_matrix
            io_constraints.append(row[0])
        for item in self.products.keys():
            num = self.item_to_enum[item]
            row = np.zeros(row_shape)
            row[0, num] = -1
            row = row @ net_item_matrix
            io_constraints.append(row[0])
        a_ub = np.array(io_constraints)
        b_ub = np.zeros(len(io_constraints))

        # Collect the rows of k that are balanced-necessary items into A_eq
        a_eq = net_item_matrix[balanced_items]
        b_eq = np.zeros(len(balanced_items))

        bounds = []
        for process in self.processes:
            bounds.append((0.0, float(process.quantity)))

        return linprog(c, a_ub, b_ub, a_eq, b_eq, bounds)

    def analyze_results(
        self, result: OptimizeResult, net_item_matrix: np.ndarray
    ) -> None:
        """Reports on the results"""

        if not result.success:
            print("Production plan optimization failed. Analysis cannot be performed.")
            print(f"Error message: {result.message}")
            return

        production_ratios: np.ndarray = result.x
        production_quantities: np.ndarray = net_item_matrix @ production_ratios

        print("\n--- Production Plan Analysis ---")

        self.perform_throughput_analysis(production_quantities)

        self.perform_bottleneck_analysis(production_ratios)

        self.perform_unused_capacity_analysis(production_ratios)

        print("\n--- Analysis Complete ---")

    def perform_throughput_analysis(self, production_quantities: np.ndarray) -> None:
        """Reports on the throughput analysis"""
        print("\n--- Throughput ---")
        print("Factory produces:")
        for item in self.products.keys():
            print(f"\t{production_quantities[self.item_to_enum[item]]} {item}")
        print("per time unit\n")
        print("Factory consumes:")
        for item in self.materials:
            print(f"\t{production_quantities[self.item_to_enum[item]]} {item}")
        print("per time unit\n")

    def perform_bottleneck_analysis(self, production_ratios: np.ndarray) -> None:
        """Bottleneck Analysis"""
        print("\n--- Bottlenecks ---")
        bottlenecks = []
        for i, process in enumerate(self.processes):
            capacity_utilization = production_ratios[i] / process.quantity
            if capacity_utilization > 0.95:  # Define "bottleneck" as > 95% utilization
                bottlenecks.append((process.name, capacity_utilization))
            print(
                f"  {process.name}: Utilization = {capacity_utilization:.2f} "
                f"(Max: {process.quantity})"
            )

        # We won't count bottlenecks if they're most of the
        # factory (i.e. it's actually just well proportioned)
        if bottlenecks and len(bottlenecks) <= (0.80 * len(self.processes)):
            print("\n  Potential Bottlenecks:")
            for process_name, utilization in bottlenecks:
                print(f"    {process_name}: {utilization:.2f}")
        else:
            print("  No significant bottlenecks detected.")

    def perform_unused_capacity_analysis(self, production_ratios: np.ndarray) -> None:
        """Unused Capacity"""
        print("\n--- Unused Capacity ---")
        total_unused_capacity = 0
        for i, process in enumerate(self.processes):
            unused_capacity = process.quantity - production_ratios[i]
            total_unused_capacity += unused_capacity
            print(f"  {process.name}: Unused = {unused_capacity:.2f}")
        print(f"  Total Unused Capacity: {total_unused_capacity:.2f}")
