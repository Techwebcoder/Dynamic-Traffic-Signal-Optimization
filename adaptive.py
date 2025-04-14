import random
from TrafficSimulator.simulation import Simulation
from TrafficSimulator.Setups import two_way_intersection_setup
from DefaultCycles.default_cycles_utils import get_fixed_cycle_actions
from Search import search_algorithm  # Assuming this exists and is correctly imported
from ReinforcementLearning.q_learning_agent import QLearningAgent
from TrafficSimulator.lqf import get_lqf_control as actual_lqf

# --- Thresholds (Adjust as needed) ---
LOW_VEHICLE_THRESHOLD = 30
MEDIUM_VEHICLE_THRESHOLD = 70
HIGH_VEHICLE_THRESHOLD = 120
HIGH_AVG_WAIT_THRESHOLD = 30  # seconds
VERY_HIGH_AVG_WAIT_THRESHOLD = 60  # seconds

class AdaptiveController:
    def __init__(self, episodes, render, queue_threshold, fc_duration, enable_merging):
        self.episodes = episodes
        self.render = render
        self.queue_threshold = queue_threshold
        self.fc_duration = fc_duration
        self.enable_merging = enable_merging
        self.control_history = []
        self.fixed_cycle_iterator = None
        self.q_learning_actions = [True, False]  # Example: True to switch phase, False to keep current
        self.q_learning_agent = QLearningAgent(actions=self.q_learning_actions, alpha=0.2, epsilon=0.9, discount=0.9)

    def get_current_state(self, simulator):
        # Implement a more sophisticated state representation based on your simulation
        return tuple([len([v for v in road.vehicles if v.v < 0.1]) for road in simulator.roads])

    def get_action_from_search(self, simulator):
        state = self.get_current_state(simulator)
        return search_algorithm(state, simulator.traffic_signals, simulator.roads) # Example

    def get_action_from_q_learning(self, simulator):
        state = self.get_current_state(simulator)
        return self.q_learning_agent.get_action(state)

    def run_episode(self, episode_num):
        simulator = two_way_intersection_setup(enable_merging=self.enable_merging)
        if self.render:
            simulator.init_gui()
        total_wait_time = 0
        steps = 0
        current_control = "fc"
        vehicle_entry_times = {}
        self.fixed_cycle_iterator = get_fixed_cycle_actions(fixed_duration=self.fc_duration)
        last_state = None
        last_action = None

        print(f"Episode {episode_num}, Step {steps + 1}: Initial Algorithm - {current_control.upper()}")
        if self.render:
            simulator.set_current_algorithm(current_control.upper())

        while not simulator.completed and not simulator.gui_closed:
            num_vehicles = simulator.n_vehicles_on_map
            waiting_vehicles = [v for i in simulator.non_empty_roads for v in simulator.roads[i].vehicles if v.v < 0.1 and hasattr(v, 'leading_vehicle') and v.leading_vehicle]
            current_wait_times = [simulator.t - vehicle_entry_times.get(v.id, simulator.t) for v in waiting_vehicles]
            avg_wait = sum(current_wait_times) / len(current_wait_times) if current_wait_times else 0
            current_state = self.get_current_state(simulator)

            self.control_history.append(current_control)
            print(f"Episode {episode_num}, Step {steps + 1}: Current Algorithm - {current_control.upper()}, Vehicles: {num_vehicles}, Avg Wait: {avg_wait:.2f}")
            if self.render:
                simulator.set_current_algorithm(current_control.upper())

            action = None
            if current_control == "fc":
                switch_signal = self.get_next_fixed_cycle_action()
                action = switch_signal if switch_signal is not None else False
                if num_vehicles > MEDIUM_VEHICLE_THRESHOLD or avg_wait > HIGH_AVG_WAIT_THRESHOLD:
                    current_control = "lqf"
            elif current_control == "lqf":
                action = actual_lqf(simulator.roads, simulator.traffic_signals)
                if num_vehicles > HIGH_VEHICLE_THRESHOLD or avg_wait > VERY_HIGH_AVG_WAIT_THRESHOLD:
                    current_control = "search"
                elif num_vehicles < LOW_VEHICLE_THRESHOLD and avg_wait < HIGH_AVG_WAIT_THRESHOLD / 2:
                    current_control = "fc"
                    self.fixed_cycle_iterator = get_fixed_cycle_actions(fixed_duration=self.fc_duration)
            elif current_control == "search":
                action = self.get_action_from_search(simulator)
                if avg_wait > VERY_HIGH_AVG_WAIT_THRESHOLD * 1.5:
                    current_control = "qlearning"
                elif num_vehicles < MEDIUM_VEHICLE_THRESHOLD and avg_wait < HIGH_AVG_WAIT_THRESHOLD:
                    current_control = "lqf"
            elif current_control == "qlearning":
                action = self.get_action_from_q_learning(simulator)

                if last_state is not None and last_action is not None:
                    reward = -avg_wait
                    self.q_learning_agent.update(last_state, last_action, current_state, reward)

                last_state = current_state
                last_action = action

                if num_vehicles < HIGH_VEHICLE_THRESHOLD and avg_wait < VERY_HIGH_AVG_WAIT_THRESHOLD:
                    current_control = "search"
                elif num_vehicles < LOW_VEHICLE_THRESHOLD and avg_wait < HIGH_AVG_WAIT_THRESHOLD / 2:
                    current_control = "fc"
                    self.fixed_cycle_iterator = get_fixed_cycle_actions(fixed_duration=self.fc_duration)

            simulator.run(action)
            total_wait_time += avg_wait * simulator.dt
            steps += 1

            for v in waiting_vehicles:
                if v.id not in vehicle_entry_times:
                    vehicle_entry_times[v.id] = simulator.t
            vehicles_departed_ids = [vid for vid in list(vehicle_entry_times.keys()) if not any(v.id == vid for i in simulator.non_empty_roads for v in simulator.roads[i].vehicles)]
            for vid in vehicles_departed_ids:
                del vehicle_entry_times[vid]

            if self.render and simulator.gui_closed:
                break

        return total_wait_time / steps if steps > 0 else 0, simulator.collision_detected

    def run(self):
        episode_wait_times = []
        episode_collisions = []

        for episode in range(1, self.episodes + 1):
            print(f"Episode {episode}")
            wait_time, collision = self.run_episode(episode)
            episode_wait_times.append(wait_time)
            episode_collisions.append(collision)
            print(f"Episode {episode} - Average Wait Time: {wait_time:.2f} seconds, Collisions: {collision}")
            self.q_learning_agent.epsilon = 0.9  # Reset exploration rate per episode (optional)

        print("\n--- Summary ---")
        print(f"Average Wait Time over {self.episodes} episodes: {sum(episode_wait_times) / self.episodes:.2f} seconds")
        print(f"Total Collisions over {self.episodes} episodes: {sum(episode_collisions)}")

    def get_next_fixed_cycle_action(self):
        if self.fixed_cycle_iterator is None:
            print("Error: Fixed cycle iterator not initialized. This should not happen in adaptive mode.")
            return None
        try:
            return next(self.fixed_cycle_iterator)
        except StopIteration:
            self.fixed_cycle_iterator = get_fixed_cycle_actions(fixed_duration=self.fc_duration)
            return next(self.fixed_cycle_iterator)