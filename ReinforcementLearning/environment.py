from typing import Optional, List, Tuple

from TrafficSimulator import Simulation
from TrafficSimulator.Setups import two_way_intersection_setup


class Environment:
    def __init__(self):
        self.action_space: List = [0, 1]
        self.sim: Optional[Simulation] = None
        self.max_gen: int = 50
        self._vehicles_on_inbound_roads: int = 0

    def step(self, step_action) -> Tuple[Tuple, float, bool, bool]:
        self.sim.run(step_action)

        new_state: Tuple = self.get_state()

        step_reward: float = self.get_reward(new_state)

        # Set the number of vehicles on inbound roads in the new state
        n_west_east_vehicles = sum(len(road.vehicles) for road in self.sim.roads[0:2])  # Assuming first two roads are W-E
        n_south_north_vehicles = sum(len(road.vehicles) for road in self.sim.roads[2:4]) # Assuming next two are S-N
        self._vehicles_on_inbound_roads = n_west_east_vehicles + n_south_north_vehicles

        # Whether a terminal state (as defined under the MDP of the task) is reached.
        terminated: bool = self.sim.completed

        # Whether a truncation condition outside the scope of the MDP is satisfied.
        # Ends the episode prematurely before a terminal state is reached.
        truncated: bool = self.sim.gui_closed

        return new_state, step_reward, terminated, truncated

    def get_state(self) -> Tuple:
        """ A state is a tuple: (traffic_signal_state, n_west_east, n_south_north, non_empty) """
        if self.sim is None or not self.sim.traffic_signals:
            return (0, 0, 0, False)  # Return a default state if simulation not initialized

        traffic_signal = self.sim.traffic_signals[0]  # Assuming a single traffic signal for a two-way intersection
        traffic_signal_state = traffic_signal.current_cycle[0]

        # Assuming roads 0 and 1 are West-East directions, and 2 and 3 are South-North
        n_west_east_vehicles = sum(len(road.vehicles) for road in self.sim.roads[0:2])
        n_south_north_vehicles = sum(len(road.vehicles) for road in self.sim.roads[2:4])

        out_bound_vehicles = sum(len(self.sim.roads[i].vehicles) for i in self.sim.outbound_roads)
        non_empty_junction = bool(self.sim.n_vehicles_on_map - out_bound_vehicles -
                                    n_west_east_vehicles - n_south_north_vehicles)

        return (traffic_signal_state, n_west_east_vehicles, n_south_north_vehicles, non_empty_junction)

    def get_reward(self, state: Tuple) -> float:
        """ Check whether the flow change is positive or negative using the difference
        in the number of vehicles in the inbound roads from the previous state """
        traffic_signal_state, n_west_east_vehicles, n_south_north_vehicles, non_empty_junction = state
        # self._vehicles_on_inbound_roads holds the data from the previous state
        flow_change = self._vehicles_on_inbound_roads - n_west_east_vehicles - n_south_north_vehicles
        return flow_change

    def reset(self, render=False) -> Tuple:
        self.sim = two_way_intersection_setup(self.max_gen)
        if render:
            self.sim.init_gui()
        init_state = self.get_state()
        self._vehicles_on_inbound_roads = sum(len(road.vehicles) for road in self.sim.roads[0:4]) if self.sim else 0 # Initialize based on initial setup
        return init_state