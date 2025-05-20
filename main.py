"""main.py
The main script file
Teo Fontana 2025, CIST 5B
"""

import json
from typing import List, Dict, Any
from sys import argv

from simulator import Factory, Process, Items


def load_factory_from_json(filename: str) -> Factory:
    """Loads a Factory object from a JSON file.

    Args:
        filename (str): The name of the JSON file to load.

    Returns:
        Factory: The Factory object loaded from the JSON file.
    """

    with open(filename, "r") as f:
        data = json.load(f)

    materials = data["materials"]
    products = data["products"]
    processes_data = data["processes"]

    processes: List[Process] = []
    for p_data in processes_data:
        processes.append(
            Process(
                p_data["name"],
                p_data["inputs"],
                p_data["outputs"],
                p_data["quantity"],
                p_data["time_per_op"],
            )
        )

    return Factory(materials, products, processes)


def save_factory_to_json(factory: Factory, filename: str) -> None:
    """Saves a Factory object to a JSON file.

    Args:
        factory (Factory): The Factory object to save.
        filename (str): The name of the JSON file to save to.
    """

    data: Dict[str, Any] = {
        "materials": factory.materials,
        "products": factory.products,
        "processes": [
            {
                "name": p.name,
                "inputs": p.inputs,
                "outputs": p.outputs,
                "quantity": p.quantity,
                "time_per_op": p.time_per_op,
            }
            for p in factory.processes
        ],
    }

    with open(filename, "w") as f:
        json.dump(data, f, indent=4)


def create_blank_factory() -> Factory:
    """Creates a blank Factory object."""
    return Factory(materials=[], products={}, processes=[])


def display_factory_info(factory: Factory) -> None:
    """Displays information about the factory (materials, products, processes)."""

    print("\n--- Factory Information ---")
    print("\n--- Materials ---")
    if factory.materials:
        for material in factory.materials:
            print(f"  - {material}")
    else:
        print("  No materials defined.")

    print("\n--- Products ---")
    if factory.products:
        for product in factory.products:
            print(f"  - {product}")
    else:
        print("  No products defined.")

    print("\n--- Processes ---")
    if factory.processes:
        for i, process in enumerate(factory.processes):
            print(f"\n  --- Process {i + 1}: {process.name} ---")
            print(f"    Inputs: {process.inputs}")
            print(f"    Outputs: {process.outputs}")
            print(f"    Quantity: {process.quantity}")
            print(f"    Time per Operation: {process.time_per_op}")
    else:
        print("  No processes defined.")


def get_user_input(prompt: str) -> str:
    """Gets user input from the console."""
    return input(prompt).strip()


def get_user_int_input(prompt: str) -> int | None:
    """Gets an int from user console input"""
    while True:
        val = get_user_input(prompt + "(whole number) ")
        if not val:
            return None
        try:
            return int(val)
        except ValueError:
            print("Please enter a whole number! (empty to cancel)")


def get_user_float_input(prompt: str) -> float | None:
    """Gets an int from user console input"""
    while True:
        val = get_user_input(prompt + "(real number) ")
        if not val:
            return None
        try:
            return float(val)
        except ValueError:
            print("Please enter a real number! (empty to cancel)")


def add_material(factory: Factory) -> None:
    """Adds a new material to the factory."""

    material_name = get_user_input("Enter material name: ")
    if material_name:
        factory.materials.append(material_name)
        print(f"Material '{material_name}' added.")
    else:
        print("Material name cannot be empty.")


def add_product(factory: Factory) -> None:
    """Adds a new product to the factory."""

    product_name = get_user_input("Enter product name: ")
    if not product_name:
        print("Product name cannot be empty.")
        return
    product_ratio = get_user_float_input("What product ratio is desired? ")
    if product_ratio is None or product_ratio < 0.0:
        print("A product requires a positive ratio.")
        return
    factory.products[product_name] = product_ratio
    print(f"Product '{product_name}' with {product_ratio} ratio added.")


def add_process(factory: Factory) -> None:
    """Adds a new process to the factory."""

    process_name = get_user_input("Enter process name: ")

    if not process_name:
        print("Exiting...")
        return

    inputs: Items = {}
    outputs: Items = {}
    quantity = get_user_float_input("Enter process quantity: ")
    time_per_op = get_user_float_input("Enter process time per operation: ")

    if quantity is None or time_per_op is None:
        print("Exiting...")
        return
    if quantity < 0:
        print("Quantity must be positive")
        return
    if time_per_op < 0:
        print("Time per operation must be positive")
        return

    print("\nEnter inputs (item name, quantity). Enter 'done' when finished.")
    while True:
        item_name = get_user_input("  Item name: ")
        if item_name.lower() == "done":
            break
        quantity = get_user_float_input("  Quantity: ")
        if item_name and quantity is not None:
            inputs[item_name] = quantity
        else:
            print("  Invalid input. Skipping. (type 'done' when finished)")

    print("\nEnter outputs (item name, quantity). Enter 'done' when finished.")
    while True:
        item_name = get_user_input("  Item name: ")
        if item_name.lower() == "done":
            break
        quantity = get_user_float_input("  Quantity: ")
        if item_name and quantity is not None:
            outputs[item_name] = quantity
        else:
            print("  Invalid input. Skipping. (type 'done' when finished)")

    factory.processes.append(
        Process(process_name, inputs, outputs, quantity, time_per_op)
    )
    print(f"Process '{process_name}' added.")


def edit_process(factory: Factory) -> None:
    """CLI Edits a processes"""
    print("\nProcess Editor:\n")
    print("Choose a process to edit:")
    for idx, process in enumerate(factory.processes):
        print(f"  {idx}. {process.name}")
    choice_range = len(factory.processes)
    choice: int | None = None
    while True:
        choice = get_user_int_input("Make a choice: ")
        if choice is None:
            print("Exiting...")
            return
        if 0 <= choice < choice_range:
            print(f"Selected process {choice}: {factory.processes[choice]}\n")
            break
        print("Please select an answer in range (leave empty to cancel)")

    process = factory.processes[choice]
    pid = choice
    while True:
        print(f"Editing proccess {process.name}")
        print("0. Exit")
        print("1. Add/Edit Input")
        print("2. Add/Edit Output")
        print("3. Remove Inputs")
        print("4. Remove Outputs")
        print("5. Change Name")
        print("6. Change Quantity")
        print("7. Change Time Per Operation")
        print("8. View Process")

        choice = get_user_input("Choose: ")
        match choice:
            case "0":
                break
            case "1":
                # Add Inputs
                add_process_input(process)
            case "2":
                # Add Outputs
                add_process_output(process)
            case "3":
                # Remove Inputs
                remove_process_input(process)
            case "4":
                # Remove Outputs
                remove_process_output(process)
            case "5":
                # Change Name
                new_name = get_user_input("New name: ")
                if new_name:
                    process.name = new_name
            case "6":
                # Change Quantity
                while True:
                    quantity = get_user_float_input("New quantity: ")
                    if quantity is None:
                        print("Cancelling...")
                        break
                    if quantity > 0:
                        break
                    print("Quantity must be postive!")
                if quantity is not None:
                    process.quantity = quantity
            case "7":
                # Change Time Per Operation
                while True:
                    tpo = get_user_float_input("New time per operation: ")
                    if tpo is None:
                        print("Cancelling...")
                        break
                    if tpo > 0:
                        break
                    print("Time per operation must be postive!")
                if tpo is not None:
                    process.time_per_op = tpo
            case "8":
                print(f'\n  --- Process "{process.name}" ---')
                print(f"    Inputs: {process.inputs}")
                print(f"    Outputs: {process.outputs}")
                print(f"    Quantity: {process.quantity}")
                print(f"    Time per Operation: {process.time_per_op}")
            case _:
                print("Invalid choice. Please try again.")

    factory.processes[pid] = process


def add_process_input(process: Process):
    """CLI Hot-adds an input to a process"""
    print("Adding an input (empty to cancel):")
    item = get_user_input("Item: ")
    if not item:
        print("Cancelling...")
        return
    while True:
        amount = get_user_float_input("Amount: ")
        if not amount:
            print("Cancelling...")
            return
        if amount > 0.0:
            break
        print("Amount must be positive!")

    process.inputs[item] = amount


def add_process_output(process: Process):
    """CLI Hot-adds an output to a process"""
    print("Adding an output (empty to cancel):")
    item = get_user_input("Item: ")
    if not item:
        print("Cancelling...")
        return
    while True:
        amount = get_user_float_input("Amount: ")
        if not amount:
            print("Cancelling...")
            return
        if amount > 0.0:
            break
        print("Amount must be positive!")

    process.inputs[item] = amount


def remove_process_input(process: Process):
    """CLI removes an input"""
    print("Removing an input (empty to cancel):")
    item = get_user_input("Item: ")
    if not item:
        print("Cancelling...")
        return
    if item not in process.inputs:
        print("Input not found in process! Cancelling...")
        return
    process.inputs.pop(item)


def remove_process_output(process: Process):
    """CLI removes an input"""
    print("Removing an output (empty to cancel):")
    item = get_user_input("Item: ")
    if not item:
        print("Cancelling...")
        return
    if item not in process.outputs:
        print("Output not found in process! Cancelling...")
        return
    process.outputs.pop(item)


def main():
    """Main function to run the factory simulation CLI."""

    factory: Factory = None

    if len(argv) > 1:
        filename = argv[1]
    else:
        filename = "factory.json"  # Default filename

    # Load factory or create a new one
    try:
        factory = load_factory_from_json(filename)
        print(f"Loaded factory from '{filename}'.")
    except FileNotFoundError:
        factory = create_blank_factory()
        print("Created a new blank factory.")
    except json.JSONDecodeError:
        factory = create_blank_factory()
        print(f"Error loading '{filename}'. Created a new blank factory.")

    while True:
        print("\n--- Factory Simulation CLI ---")
        print("0. Exit")
        print("1. Display Factory Info")
        print("2. Add Material")
        print("3. Add Product")
        print("4. Add Process")
        print("5. Run Simulation and Analyze")
        print("6. Save Factory")
        print("7. Load Factory")
        print("8. Edit processes")

        choice = get_user_input("Enter your choice: ")

        if choice == "0":
            print("Exiting.")
            break
        elif choice == "1":
            display_factory_info(factory)
        elif choice == "2":
            add_material(factory)
        elif choice == "3":
            add_product(factory)
        elif choice == "4":
            add_process(factory)
        elif choice == "5":
            try:
                factory.calculate()  # Run the simulation
            except ValueError as e:
                print(f"Error during simulation: {e}")
        elif choice == "6":
            save_factory_to_json(factory, filename)
            print(f"Factory saved to '{filename}'.")
        elif choice == "7":
            new_filename = get_user_input("Enter filename to load: ")
            if new_filename:
                try:
                    factory = load_factory_from_json(new_filename)
                    filename = new_filename
                    print(f"Loaded factory from '{filename}'.")
                except FileNotFoundError:
                    print(f"File '{new_filename}' not found.")
                except json.JSONDecodeError:
                    print(f"Error loading '{new_filename}'.")
            else:
                print("Filename cannot be empty.")
        elif choice == "8":
            edit_process(factory)
        else:
            print("Invalid choice. Please try again.")


if __name__ == "__main__":
    main()
