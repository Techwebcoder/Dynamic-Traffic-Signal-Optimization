# main.py
import argparse
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from ReinforcementLearning import Environment  # Import Environment
from ReinforcementLearning import q_learning  # Import Q-learning function
from Search import search  # Import Search function
from TrafficSimulator.lqf import get_lqf_control as actual_lqf  # Rename to avoid conflict
from TrafficSimulator.simulation import Simulation  # Correct import
from TrafficSimulator.Setups import two_way_intersection_setup
import time  # For tracking waiting times
from DefaultCycles.default_cycles_utils import default_cycle, get_fixed_cycle_actions  # Corrected import
import random
import adaptive  # Import the adaptive control module

# --- Global Thresholds (Adjust as needed) ---
LOW_VEHICLE_THRESHOLD = 30
MEDIUM_VEHICLE_THRESHOLD = 70
HIGH_VEHICLE_THRESHOLD = 120
HIGH_AVG_WAIT_THRESHOLD = 30  # seconds
VERY_HIGH_AVG_WAIT_THRESHOLD = 60  # seconds

def main():
    """
    Main function to parse command-line arguments and run the traffic flow optimizer.
    """
    parser = argparse.ArgumentParser(description="Traffic Flow Optimizer")
    methods = ['fc', 'lqf', 'search', 'qlearning', 'adaptive']

    parser.add_argument("-m", "--method", choices=methods, required=True,
                        help="Optimization method: fc, lqf, search, qlearning, adaptive")
    parser.add_argument("-e", "--episodes", metavar='N', type=int, default=1,
                        help="Number of evaluation episodes to run (default: 1)")
    parser.add_argument("-r", "--render", action='store_true',
                        help="Displays the simulation window")
    parser.add_argument("--queue_threshold", type=int, default=5,
                        help="Queue length threshold (not directly used in adaptive)")
    parser.add_argument("--fc_duration", type=int, default=15,
                        help="Duration of each phase in Fixed Cycle mode")
    parser.add_argument("--enable_merging", action='store_true',
                        help="Enable merging behavior in the simulation")

    args = parser.parse_args()

    if args.method == 'fc':
        from DefaultCycles.default_cycles_utils import default_cycle
        default_cycle(n_episodes=args.episodes, action_func_name='fc', render=args.render, fixed_duration=args.fc_duration)
    elif args.method == 'lqf':
        from DefaultCycles.default_cycles_utils import default_cycle
        default_cycle(n_episodes=args.episodes, action_func_name='lqf', render=args.render)
    elif args.method == 'search':
        search(episodes=args.episodes, render=args.render)
    elif args.method == 'qlearning':
        q_learning(n_episodes=args.episodes, render=args.render)
    elif args.method == 'adaptive':
        print(f"Running Adaptive Control method for {args.episodes} episodes...")
        adaptive_controller = adaptive.AdaptiveController(
            episodes=args.episodes,
            render=args.render,
            queue_threshold=args.queue_threshold,
            fc_duration=args.fc_duration,
            enable_merging=args.enable_merging
        )
        adaptive_controller.run()
    else:
        print(f"Error: Unknown method '{args.method}'")

    plt.figure()
    plt.plot([1, 2, 3, 4], [1, 4, 9, 16])
    plt.savefig("simulation_output.png")
    plt.close()

    print("simulation_output.png")

if __name__ == "__main__":
    main()