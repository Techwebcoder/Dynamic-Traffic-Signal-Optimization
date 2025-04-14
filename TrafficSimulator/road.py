from collections import deque
from typing import Deque, Optional, Tuple

from scipy.spatial import distance

# Use forward reference for TrafficSignal to break circular import
class Road:
    def __init__(self, start: Tuple[int, int], end: Tuple[int, int], index: int):
        self.start = start
        self.end = end
        self.index = index

        self.vehicles: Deque[Vehicle] = deque()

        self.length: float = distance.euclidean(self.start, self.end)
        self.angle_sin: float = (self.end[1] - self.start[1]) / self.length
        self.angle_cos: float = (self.end[0] - self.start[0]) / self.length

        self.has_traffic_signal: bool = False
        self.traffic_signal: Optional["TrafficSignal"] = None
        self.traffic_signal_group: Optional[int] = None
        self._force_red: bool = False  # Added for manual red override

    def set_traffic_signal(self, signal: "TrafficSignal", group: int):
        self.has_traffic_signal = True
        self.traffic_signal = signal
        self.traffic_signal_group = group
        self._force_red = False  # Reset manual override when a signal is set

    def __str__(self):
        return f'Road {self.index}'

    @property
    def traffic_signal_state(self):
        """ Returns the traffic signal state if the road has a traffic signal, else True"""
        if self._force_red:
            return False
        if self.has_traffic_signal:
            i = self.traffic_signal_group
            return self.traffic_signal.current_cycle[i]
        return True

    def force_red(self):
        """Forces the traffic signal on this road to behave as red."""
        self._force_red = True

    def unforce_red(self):
        """Releases the forced red state, allowing the actual signal to control."""
        self._force_red = False

    def update(self, dt, sim_t):
        n = len(self.vehicles)
        if n > 0:
            lead: Vehicle = self.vehicles[0]

            # Check for traffic signal
            if self.has_traffic_signal:
                if self.traffic_signal_state:
                    # If traffic signal is green, let vehicles pass
                    lead.unstop(sim_t)
                    for vehicle in self.vehicles:
                        vehicle.unslow()
                else:
                    # The traffic signal is red
                    lead_can_stop_safely = lead.x <= self.length - self.traffic_signal.stop_distance / 1.5
                    if lead_can_stop_safely:
                        lead.slow(self.traffic_signal.slow_factor)  # slow vehicles in slow zone
                        lead_in_stop_zone = self.length - self.traffic_signal.stop_distance <= lead.x
                        if lead_in_stop_zone:
                            lead.stop(sim_t)
                    else:
                        # If too close to the red light, don't slow down or stop
                        lead.unslow()
                        lead.unstop(sim_t)
            else:
                # No traffic signal, ensure vehicles are not stopped or slowed unnecessarily
                lead.unslow()
                lead.unstop(sim_t)

            # Update first vehicle
            lead.update(None, dt, self)
            # Update other vehicles
            for i in range(1, n):
                lead = self.vehicles[i - 1]
                self.vehicles[i].update(lead, dt, self)

# Import Vehicle here to avoid potential circular import issues if Vehicle imports Road
from TrafficSimulator.vehicle import Vehicle
# Import TrafficSignal here after the Road class definition to resolve the forward reference
from TrafficSimulator.traffic_signal import TrafficSignal