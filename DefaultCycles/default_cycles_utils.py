from ReinforcementLearning import Environment

t = 15  # Cycle time threshold

def fixed_cycle_action(sim, dummy=None) -> bool:
    """ Returns a boolean indicating to take an action
    if enough time has elapsed since the previous action """
    switch = False
    traffic_signal = sim.traffic_signals[0]
    time_elapsed = sim.t - traffic_signal.prev_update_time >= t
    if time_elapsed:
        traffic_signal.prev_update_time = sim.t
        switch = True
    return switch

def longest_queue_action(curr_state, prev_state) -> bool:
    """ Returns a boolean indicating to take an action
    based on the longest queue and elapsed time """
    switch = False
    traffic_signal = curr_state.traffic_signals[0]
    time_elapsed = curr_state.t - traffic_signal.prev_update_time >= t
    if time_elapsed:
        traffic_signal_state, n_direction_1_vehicles, n_direction_2_vehicles, non_empty_junction = prev_state
        # If the direction with most vehicles has a red light, switch it to green
        if traffic_signal_state and n_direction_1_vehicles < n_direction_2_vehicles:
            switch = True
        elif not traffic_signal_state and n_direction_1_vehicles > n_direction_2_vehicles:
            switch = True
        if switch:
            # Update the traffic signal update time
            traffic_signal.prev_update_time = curr_state.t
    return switch

action_funcs = {'fc': fixed_cycle_action,
                'lqf': longest_queue_action}

def get_fixed_cycle_actions(fixed_duration=15):
    """Yields True/False for fixed cycle switching based on time."""
    global t
    t = fixed_duration
    sim_time = 0
    last_switch_time = -t  # Ensure the first action happens at t=0
    while True:
        if sim_time - last_switch_time >= t:
            yield True
            last_switch_time = sim_time
        else:
            yield False
        sim_time += 1

def default_cycle(n_episodes: int = 1, action_func_name: str = 'fc', render=False, fixed_duration=15):
    """Runs simulation for a fixed number of episodes with a given action function."""
    global t
    t = fixed_duration
    print(f"\n -- Running {action_func_name.upper()} for {n_episodes} episodes  -- ")
    environment: Environment = Environment()
    total_wait_time, total_collisions = 0, 0
    action_func = action_funcs[action_func_name]
    for episode in range(1, n_episodes + 1):
        state = environment.reset(render)
        score = 0
        collision_detected = 0
        done = False

        while not done:
            action = action_func(environment.sim, state)
            state, reward, done, truncated = environment.step(action)
            if truncated:
                exit()
            score += reward
            collision_detected += environment.sim.collision_detected

        if collision_detected:
            print(f"Episode {episode} - Collisions: {int(collision_detected)}")
            total_collisions += 1
        else:
            wait_time = environment.sim.current_average_wait_time
            total_wait_time += wait_time
            print(f"Episode {episode} - Wait time: {wait_time:.2f}")

    n_completed = n_episodes - total_collisions
    print(f"\n -- Results after {n_episodes} episodes: -- ")
    if n_completed > 0:
        print(f"Average wait time per completed episode: {total_wait_time / n_completed:.2f}")
    else:
        print("No episodes completed without collisions.")
    print(f"Average collisions per episode: {total_collisions / n_episodes:.2f}")