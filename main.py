#!/usr/bin/python3

from z3 import *
import argparse
import csv

def read_level(filename):
    # Open the file
    try:
        with open(filename, 'r') as f:
            reader = csv.reader(f)
            data = []
            for row_id, row in enumerate(reader):
                if row_id == 0:
                    size = int(row[0])
                else:
                    coordinates_row = [(int(item.split(" ")[0]), int(item.split(" ")[1])) for item in row]  # Convert each item in the row to an integer
                    data.append(coordinates_row)
            return (size, data)
    except FileNotFoundError:
        print(f"Error: File '{args.file}' not found.")
        exit(-1)

def handle_args():
    parser = argparse.ArgumentParser(description="Solve the mosaik puzzle using Z3 solver.")
    parser.add_argument("file", type=str, help="Path to the input file")

    # Parse command-line arguments
    return parser.parse_args()

def get_neighbors(matrix, row, col):
    # List of relative positions of the 8 neighbors
    neighbors = [
                (-1, 0),             # Top-left, Top, Top-right
        ( 0, -1)       , ( 0, 1),   # Left, Self, Right
                ( 1, 0)              # Bottom-left, Bottom, Bottom-right
    ]
    
    # List to store valid neighbors
    valid_neighbors = []
    
    # Iterate over each relative position
    for dr, dc in neighbors:
        new_row, new_col = row + dr, col + dc
        
        # Check if the new position is within bounds of the matrix
        if 0 <= new_row < len(matrix) and 0 <= new_col < len(matrix[0]):
            valid_neighbors.append(matrix[new_row][new_col])
    
    return valid_neighbors

def solve_level(size, level):
    solver = Solver()
    vars = [[Bool(f"var_{i}_{o}") for i in range(size)] for o in range(size)]
    
    # add constant constraints
    # white stones
    for coord in level[0]:
        solver.add(vars[coord[0]][coord[1]])

    # black stones
    for coord in level[1]:
        solver.add(Not(vars[coord[0]][coord[1]]))

    # add square constraint
    for row_id in range(size - 1):
        for column_id in range(size - 1):
            square_vars = [
                vars[row_id][column_id],
                vars[row_id + 1][column_id],
                vars[row_id + 1][column_id + 1],
                vars[row_id][column_id + 1]
                ]
            # not all white squares
            solver.add(Not(And(square_vars)))
            # not all black squares
            solver.add(Or(square_vars))
    
    # all white squares have either one, two, three or four orthogonal neighbours,
    chain_end_list = []
    chain_t_crossing_list = []
    chain_x_crossing_list = []
    for row_id, row in enumerate(vars):
        for column_id, var in enumerate(row):
            neighbours = get_neighbors(vars, row_id, column_id)
            neighbor_sum = Sum([If(neighbor, 1, 0) for neighbor in neighbours])
            chain_end = And(var, neighbor_sum == 1) # square is white and has one neighbours
            chain_t_crossing = And(var, neighbor_sum == 3) # square is white and has three neighbours
            chain_x_crossing = And(var, neighbor_sum == 4) # square is white and has four neighbours
            
            lone_white_square = And(var, Not(Or(neighbours)))
            
            chain_end_list.append(If(chain_end, 1, 0))
            chain_t_crossing_list.append(If(chain_t_crossing, 1, 0))
            chain_x_crossing_list.append(If(chain_x_crossing, 1, 0))
            or_list = [ # square is part of a chain or is black
                lone_white_square, 
                Not(var)
                ] 
            solver.add(Or(or_list))

    # There must be exactly two chain ends, 
    # a chain T-crossing intruduces another chain end,
    # a chain X-crossing intruduces two more chain ends,
    solver.add(
        (
            Sum(chain_end_list)
              - Sum(chain_t_crossing_list) 
              - 2 * Sum(chain_x_crossing_list)
            ) 
            == 2
         )
    
    for assertion in solver.assertions():
        print(assertion)

    # Check satisfiability
    if solver.check() == sat:
        model = solver.model()
        return [[model[square] for square in row] for row in vars]  # Return the values of the variables
    else:
        print("No solution exists")
        exit(-1)

def main():
    args = handle_args()

    size, level = read_level(args.file)
    print("White stones at:  ", end="")
    for white_stones in level[0]:
        print("(" + str(white_stones[0]) + "/" + str(white_stones[1]) + ")", end="")
    print()
    print("White stones at:  ", end="")
    for black_stones in level[1]:
        print("(" + str(black_stones[0]) + "/" + str(black_stones[1]) + ")", end="")
            
    print()

    solution = solve_level(size, level)
    for row in solution:
        for square in row:
            print("X" if square else "O", end=" ")
        print()

if __name__ == "__main__":
    main()