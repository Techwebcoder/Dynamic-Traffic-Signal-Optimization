from itertools import chain
from typing import List, Dict, Tuple, Set, Optional
import tkinter as tk
import pygame

from scipy.spatial import distance

from TrafficSimulator.road import Road
from TrafficSimulator.traffic_signal import TrafficSignal
from TrafficSimulator.vehicle_generator import VehicleGenerator
from TrafficSimulator.window import Window


class Simulation:
    def __init__(self, max_gen: int = None):
        self.t = 0.0
        self.dt = 1 / 60
        self.roads: List[Road] = []
        self.generators: List[VehicleGenerator] = []
        self.traffic_signals: List[TrafficSignal] = []

        self.collision_detected: bool = False
        self.n_vehicles_generated: int = 0
        self.n_vehicles_on_map: int = 0

        self._gui: Optional[Window] = None
        self._current_algorithm_text: str = "LQf"  # Initial algorithm name

        self._non_empty_roads: Set[int] = set()
        self._inbound_roads: Set[int] = set()
        self._outbound_roads: Set[int] = set()

        self._intersections: Dict[int, Set[int]] = {}
        self.max_gen: Optional[int] = max_gen
        self._waiting_times_sum: float = 0

        self._search_start_time = 20  # Example: Switch to "Search" after 20 seconds
        self._q_learning_start_vehicles = 50  # Example: Switch to "Q-learning" after 50 vehicles generated
        self._algorithm_state = "LQf"  # Keep track of the current algorithm state

        self._last_algorithm_change_time: float = 0.0
        self._displayed_algorithm_name: str = "LQf"
        self._algorithm_display_duration: float = 5.0  # Display for 5 seconds

    def set_current_algorithm(self, algorithm_name: str) -> None:
        if self._current_algorithm_text != algorithm_name:
            self._current_algorithm_text = algorithm_name
            self._last_algorithm_change_time = self.t
            self._displayed_algorithm_name = algorithm_name
            if self._gui:
                self._gui.update_algorithm_text(self._displayed_algorithm_name) # Update immediately
        elif self._gui and self.t - self._last_algorithm_change_time >= self._algorithm_display_duration:
            self._gui.update_algorithm_text(self._current_algorithm_text) # Revert if duration passed

    def add_intersections(self, intersections_dict: Dict[int, Set[int]]) -> None:
        self._intersections.update(intersections_dict)

    def add_road(self, start: Tuple[int, int], end: Tuple[int, int]) -> None:
        road = Road(start, end, index=len(self.roads))
        self.roads.append(road)

    def add_roads(self, roads: List[Tuple[int, int]]) -> None:
        for road in roads:
            self.add_road(*road)

    def add_generator(self, vehicle_rate, paths: List[List]) -> None:
        inbound_roads: List[Road] = [self.roads[roads[0]] for weight, roads in paths]
        inbound_dict: Dict[int: Road] = {road.index: road for road in inbound_roads}
        vehicle_generator = VehicleGenerator(vehicle_rate, paths, inbound_dict)
        self.generators.append(vehicle_generator)

        for (weight, roads) in paths:
            self._inbound_roads.add(roads[0])
            self._outbound_roads.add(roads[-1])

    def add_traffic_signal(self, roads: List[List[int]], cycle: List[Tuple[bool, ...]],
                           slow_distance: float, slow_factor: float, stop_distance: float) -> None:
        from TrafficSimulator.traffic_signal import TrafficSignal
        traffic_signal = TrafficSignal(roads, cycle, slow_distance, slow_factor, stop_distance, self.roads)
        self.traffic_signals.append(traffic_signal)

    @property
    def gui_closed(self) -> bool:
        return self._gui and self._gui.closed

    @property
    def non_empty_roads(self) -> Set[int]:
        return self._non_empty_roads

    @property
    def completed(self) -> bool:
        if self.max_gen:
            return self.collision_detected or (self.n_vehicles_generated == self.max_gen
                                                and not self.n_vehicles_on_map)
        return self.collision_detected

    @property
    def intersections(self) -> Dict[int, Set[int]]:
        output: Dict[int, Set[int]] = {}
        non_empty_roads: Set[int] = self._non_empty_roads
        for road_index in non_empty_roads:
            if road_index in self._intersections:
                intersecting_roads = self._intersections[road_index].intersection(non_empty_roads)
                if intersecting_roads:
                    output[road_index] = intersecting_roads
        return output

    @property
    def current_average_wait_time(self) -> float:
        on_map_wait_time = 0
        completed_wait_time = 0
        n_completed_journey = self.n_vehicles_generated - self.n_vehicles_on_map
        if n_completed_journey:
            completed_wait_time = round(self._waiting_times_sum / n_completed_journey, 2)
        if self.n_vehicles_on_map:
            total_on_map_wait_time = sum(vehicle.get_wait_time(self.t) for i in self.non_empty_roads
                                        for vehicle in self.roads[i].vehicles)
            on_map_wait_time = total_on_map_wait_time / self.n_vehicles_on_map if self.n_vehicles_on_map > 0 else 0
        return completed_wait_time + on_map_wait_time

    @property
    def inbound_roads(self) -> Set[int]:
        return self._inbound_roads

    @property
    def outbound_roads(self) -> Set[int]:
        return self._outbound_roads

    def init_gui(self) -> None:
        if not self._gui:
            self._gui = Window(self)
        self._gui.update()
        self._gui.update_algorithm_text(self._displayed_algorithm_name)

    def run(self, action: Optional[int] = None) -> None:
        n = 180  # 3 simulation seconds
        if action is not None:
            self._update_signals(action)
            self._loop(n)
            if self.collision_detected or self.gui_closed:
                return
            self._update_signals(action)
            if self.completed or self.gui_closed:
                return
        self._loop(n)

    def update(self) -> None:
        # Debugging print
        # print(f"Simulation time: {self.t}, Current Algorithm: {self._current_algorithm_text}, Displayed: {self._displayed_algorithm_name}, Last Change: {self._last_algorithm_change_time}")

        if self._algorithm_state == "LQf" and self.t >= 20:
            print(f"Switching algorithm to Search at time: {self.t}")
            self.set_current_algorithm("Search")
            self._algorithm_state = "Search"

        elif self._algorithm_state == "Search" and self.n_vehicles_generated >= 50:
            print(f"Switching algorithm to Q-learning after {self.n_vehicles_generated} vehicles generated")
            self.set_current_algorithm("Q-learning")
            self._algorithm_state = "Q-learning"
        else:
            # Ensure the displayed name reflects the current algorithm after the display duration
            if self.t - self._last_algorithm_change_time >= self._algorithm_display_duration and self._displayed_algorithm_name != self._current_algorithm_text:
                self._displayed_algorithm_name = self._current_algorithm_text
                if self._gui:
                    self._gui.update_algorithm_text(self._displayed_algorithm_name)

        for i in self._non_empty_roads:
            self.roads[i].update(self.dt, self.t)

        for gen in self.generators:
            if self.max_gen and self.n_vehicles_generated == self.max_gen:
                break
            road_index = gen.update(self.t, self.n_vehicles_generated)
            if road_index is not None:
                self.n_vehicles_generated += 1
                self.n_vehicles_on_map += 1
                self._non_empty_roads.add(road_index)

        for road_index in list(self._non_empty_roads):
            if not self.roads[road_index].vehicles:
                self._non_empty_roads.discard(road_index)

        self._check_out_of_bounds_vehicles()
        self._detect_collisions()
        self.t += self.dt
        if self._gui:
            self._gui.update()

    def _loop(self, n: int) -> None:
        for _ in range(n):
            self.update()
            if self.completed or self.gui_closed:
                return

    def _update_signals(self, action: int) -> None:
        for i, signal in enumerate(self.traffic_signals):
            if i == action:
                signal.update()
        if self._gui:
            self._gui.update()

    def _detect_collisions(self) -> None:
        radius = 3
        for main_road_index in self._non_empty_roads:
            if main_road_index in self._intersections:
                main_road = self.roads[main_road_index]
                intersecting_road_indices = self._intersections[main_road_index].intersection(self._non_empty_roads)
                for vehicle in main_road.vehicles:
                    for intersecting_road_index in intersecting_road_indices:
                        intersecting_road = self.roads[intersecting_road_index]
                        for intersecting in intersecting_road.vehicles:
                            if distance.euclidean(vehicle.position, intersecting.position) < radius:
                                self.collision_detected = True
                                return

    def _check_out_of_bounds_vehicles(self):
        new_non_empty_roads = set()
        new_empty_roads = set()
        for i in self._non_empty_roads:
            road = self.roads[i]
            if road.vehicles:
                lead = road.vehicles[0]
                if lead.x >= road.length:
                    if lead.current_road_index + 1 < len(lead.path):
                        road.vehicles.popleft()
                        lead.x = 0
                        lead.current_road_index += 1
                        next_road_index = lead.path[lead.current_road_index]
                        new_non_empty_roads.add(next_road_index)
                        self.roads[next_road_index].vehicles.append(lead)
                        if not road.vehicles:
                            new_empty_roads.add(road.index)
                    else:
                        road.vehicles.popleft()
                        if not road.vehicles:
                            new_empty_roads.add(road.index)
                        self.n_vehicles_on_map -= 1
                        self._waiting_times_sum += lead.get_wait_time(self.t)

        self._non_empty_roads.difference_update(new_empty_roads)
        self._non_empty_roads.update(new_non_empty_roads)

    def get_state(self):
        """
        Returns the current state of the simulation (e.g., vehicle positions, speeds, signal states).
        This is a placeholder for a more complex state representation.
        """
        state = {
            'time': self.t,
            'num_vehicles': self.n_vehicles_on_map,
            'average_wait_time': self.current_average_wait_time,
            'signal_states': [signal.current_cycle for signal in self.traffic_signals],
            'vehicle_positions': {road.index: [(v.x, v.v) for v in road.vehicles] for road in self.roads if road.vehicles}
        }
        return state

if __name__ == '__main__':
    pygame.init()
    simulation = Simulation(max_gen=100)  # Example max generation
    simulation.add_roads([((100, 200), (300, 200)), ((300, 200), (300, 400))])
    simulation.add_generator(vehicle_rate=20, paths=[(1, [0, 1])])
    simulation.add_traffic_signal(roads=[[0]], cycle=[(True,), (False,)], slow_distance=30, slow_factor=0.5, stop_distance=10)
    simulation.init_gui()

    while not simulation.gui_closed and not simulation.completed and not simulation.collision_detected:
        simulation.update()
        pygame.time.delay(int(simulation.dt * 1000))

    pygame.quit()