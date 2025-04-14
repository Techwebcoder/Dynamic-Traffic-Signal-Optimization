import random
from typing import List, Dict, Optional

from numpy.random import randint

from TrafficSimulator.road import Road
from TrafficSimulator.vehicle import Vehicle


class VehicleGenerator:
    def __init__(self, vehicle_rate: float, paths: List[List], inbound_roads: Dict[int, Road]):
        self._vehicle_rate: float = vehicle_rate  # Average rate (vehicles per second)
        self._paths: List[List] = paths
        self._prev_gen_time: float = 0
        self._inbound_roads: Dict[int, Road] = inbound_roads

    def _generate_vehicle(self) -> Vehicle:
        """Returns a random vehicle with a path chosen based on weights."""
        total_weight = sum(weight for weight, path in self._paths)
        if total_weight <= 0:
            return Vehicle([])  # Return an empty path vehicle to avoid errors

        rand_val = random.uniform(0, total_weight)
        cumulative_weight = 0
        chosen_path = None
        for weight, path in self._paths:
            cumulative_weight += weight
            if rand_val < cumulative_weight:
                chosen_path = path
                break
        return Vehicle(chosen_path if chosen_path else [])

    def update(self, curr_t: float, n_vehicles_generated: int) -> Optional[int]:
        """Generates a vehicle randomly based on the vehicle rate (average).
        :return: road index if a vehicle was generated, else None
        """
        # Use an exponential distribution for random inter-arrival times
        arrival_interval = random.expovariate(self._vehicle_rate) if self._vehicle_rate > 0 else float('inf')
        time_elapsed = curr_t - self._prev_gen_time

        if time_elapsed >= arrival_interval:
            vehicle: Vehicle = self._generate_vehicle()
            if not vehicle.path:  # If no valid path was chosen
                self._prev_gen_time = curr_t
                return None

            start_road_index = vehicle.path[0]
            if start_road_index in self._inbound_roads:
                road: Road = self._inbound_roads[start_road_index]
                # Check if the road is empty or has enough space for the new vehicle
                if not road.vehicles or (road.vehicles and road.vehicles[-1].x > vehicle.s0 + vehicle.length + 5): # Added a small buffer
                    vehicle.index = n_vehicles_generated
                    road.vehicles.append(vehicle)
                    self._prev_gen_time = curr_t
                    return road.index
            else:
                self._prev_gen_time = curr_t  # Still update time even if road is invalid
                return None
        return None