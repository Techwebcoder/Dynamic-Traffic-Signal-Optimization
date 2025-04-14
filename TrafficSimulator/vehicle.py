from typing import List, Tuple

import numpy as np


class Vehicle:
    def __init__(self, path: List[int]):
        self.index = 0
        self.length = 4
        self.width = 2

        self.s0 = 4
        self.T = 1
        self.v_max = 16.6  # Max velocity
        self.a_max = 1.44  # Max positive acceleration
        self.b_max = 4.61  # Max negative acceleration
        self.sqrt_ab = 2 * np.sqrt(self.a_max * self.b_max)
        self._v_max = self.v_max

        self.v = 0  # Initial velocity set to 0
        self.a = 0  # Acceleration
        self.x = 0  # Position, relative to its current road

        self.is_stopped = False
        self._last_time_stopped = None
        self._waiting_time = 0

        self.path: List[int] = path  # Road indexes
        self.current_road_index = 0

        # Used for collision detection, value set upon adding it to the map in vehicle.update()
        self.position: Tuple = (None, None)

    def __str__(self):
        return f'Vehicle {self.index}'

    def get_wait_time(self, sim_t):
        if self.is_stopped and self._last_time_stopped is not None:
            return self._waiting_time + (sim_t - self._last_time_stopped)
        return self._waiting_time

    def update(self, lead, dt, road):
        """
        Updates the vehicle position velocity, and acceleration
        :param road: vehicle's road
        :param lead: leading vehicle in front (can be None)
        :param dt: simulation time step
        """
        # Intelligent Driver Model (IDM) for acceleration
        alpha = 0
        if lead:
            delta_x = lead.x - self.x - lead.length  # Net distance to the leading vehicle
            delta_v = self.v - lead.v                # Relative speed

            if delta_x > 0:
                alpha = (self.s0 + max(0, self.T * self.v + delta_v * self.v / self.sqrt_ab)) / delta_x
            else:
                alpha = float('inf') # Very close or behind, apply strong braking

        v_desired = self.v_max * (1 - np.exp(-(1/self.T) * self.x / self.v_max)) if not lead else self.v_max # Consider distance to end of road if no lead

        self.a = self.a_max * (1 - (self.v / self.v_max)**4 - alpha**2)

        # Apply strong braking if approaching a stopped vehicle or red light
        if self.is_stopped:
            self.a = -self.b_max * (self.v / self.v_max) if self.v > 0 else 0

        # Update velocity and position
        self.v += self.a * dt
        self.v = max(0, self.v)  # Ensure velocity doesn't go negative
        self.x += self.v * dt + 0.5 * self.a * dt * dt

        # Update position for rendering
        sin, cos = road.angle_sin, road.angle_cos
        global_x = road.start[0] + cos * self.x
        global_y = road.start[1] + sin * self.x
        self.position = (global_x, global_y)

    def stop(self, t):
        if not self.is_stopped:
            self._last_time_stopped = t
            self.is_stopped = True
            self.v = 0  # Immediately set velocity to 0 upon stopping

    def unstop(self, t):
        if self.is_stopped:
            if self._last_time_stopped is not None:
                self._waiting_time += (t - self._last_time_stopped)
            self._last_time_stopped = None
            self.is_stopped = False
            self.v = 0.1 # Give a small initial velocity to start moving

    def slow(self, traffic_light_slow_factor):
        self.v_max = self._v_max * traffic_light_slow_factor

    def unslow(self):
        self.v_max = self._v_max