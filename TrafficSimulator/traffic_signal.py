from typing import List, Tuple ,Optional
from itertools import chain

from TrafficSimulator.road import Road  # Import Road class


class TrafficSignal:
    def __init__(self, roads: List[List[int]], cycle: List[Tuple[bool, ...]],
                 slow_distance: float, slow_factor: float, stop_distance: float,
                 simulation_roads: List[Road]):
        """
        Initializes the TrafficSignal.

        Args:
            roads: A list of lists, where each inner list contains the indices of the
                   roads controlled by one phase of the traffic signal.
            cycle: A list of tuples, where each tuple represents a phase of the cycle.
                   Each element in the tuple corresponds to a road group in 'roads'.
                   True means the signal is green for that group, False means red.
            slow_distance: Distance before the stop line where vehicles start to slow.
            slow_factor: Factor by which vehicles slow down in the slow zone.
            stop_distance: Distance before the stop line where vehicles should stop.
            simulation_roads: The list of all Road objects in the simulation.
        """
        self.road_indices: List[List[int]] = roads
        self.cycle: List[Tuple[bool, ...]] = cycle
        self.current_cycle_index = 0
        self.slow_distance: float = slow_distance
        self.slow_factor: float = slow_factor
        self.stop_distance: float = stop_distance
        self.prev_update_time: float = 0

        # Assign the TrafficSignal to the corresponding Road objects
        for i, road_group_indices in enumerate(self.road_indices):
            for road_index in road_group_indices:
                if 0 <= road_index < len(simulation_roads):
                    simulation_roads[road_index].set_traffic_signal(self, i)
                else:
                    print(f"Warning: Road index {road_index} is out of bounds for traffic signal group {i}.")

    @property
    def current_cycle(self) -> Tuple[bool, ...]:
        return self.cycle[self.current_cycle_index]

    def update(self):
        self.current_cycle_index = (self.current_cycle_index + 1) % len(self.cycle)

    def set_state(self, group_index: int, state: bool):
        """
        Directly sets the state of a specific traffic signal group.

        Args:
            group_index: The index of the traffic signal group to change.
            state: True for green, False for red.
        """
        if 0 <= group_index < len(self.cycle[0]):
            current_phase_list = list(self.cycle[self.current_cycle_index])
            current_phase_list[group_index] = state
            self.cycle[self.current_cycle_index] = tuple(current_phase_list)
        else:
            print(f"Warning: Traffic signal group index {group_index} is out of bounds.")

    def get_state(self, group_index: int) -> Optional[bool]:
        """
        Returns the current state of a specific traffic signal group.

        Args:
            group_index: The index of the traffic signal group.

        Returns:
            The current state (True for green, False for red) or None if the index is invalid.
        """
        if 0 <= group_index < len(self.cycle[self.current_cycle_index]):
            return self.cycle[self.current_cycle_index][group_index]
        else:
            print(f"Warning: Traffic signal group index {group_index} is out of bounds.")
            return None