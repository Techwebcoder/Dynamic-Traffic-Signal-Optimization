from TrafficSimulator.simulation import Simulation

def get_lqf_control(simulation_state):
    """
    Implements the Longest Queue First (LQF) traffic light control strategy.

    Args:
        simulation_state (dict): A dictionary containing the current state of the simulation,
                                 including information about roads and their vehicles.
                                 It should have a 'queues' key which is a dictionary
                                 where keys are road identifiers (e.g., 'road_0_in')
                                 and values are deque objects containing the vehicles
                                 waiting on that road.

    Returns:
        int: An integer representing the action to take (the traffic light phase to activate).
             This assumes a simple two-phase traffic light system where 0 and 1 are the actions.
             The mapping of actions to traffic light groups needs to be consistent with
             how your TrafficSignal class and setup are defined.
    """
    queues = simulation_state.get('queues', {})
    if not queues:
        return 0  # Default to a safe state if no queue information

    max_queue_length = -1
    longest_queue_road_index = None

    # Assuming your inbound roads are named in a way that their index can be extracted
    # e.g., 'road_0_in', 'road_1_in', etc.
    inbound_road_indices = set()
    for road_str in queues.keys():
        try:
            index = int(road_str.split('_')[1])
            inbound_road_indices.add(index)
        except (IndexError, ValueError):
            pass

    # Determine the road with the longest queue among inbound roads
    for index in inbound_road_indices:
        queue_name = f'road_{index}_in'
        if queue_name in queues:
            queue_length = len(queues[queue_name])
            if queue_length > max_queue_length:
                max_queue_length = queue_length
                longest_queue_road_index = index

    if longest_queue_road_index is None:
        return 0  # Default action if no inbound roads found

    # Determine the traffic light phase based on the longest queue
    # This logic needs to match how your traffic signals are grouped and controlled.
    # For a simple two-phase intersection, you might assume:
    # - Roads with even indices (0, 2, ...) belong to one phase (e.g., West-East).
    # - Roads with odd indices (1, 3, ...) belong to the other phase (e.g., South-North).

    if longest_queue_road_index % 2 == 0:
        return 0  # Activate phase 0 (e.g., green for West-East)
    else:
        return 1  # Activate phase 1 (e.g., green for South-North)

    # You might need more sophisticated logic here if your intersection is more complex
    # with more than two phases or different groupings of roads per signal.

if __name__ == '__main__':
    # Example usage (this won't run a full simulation without the other components)
    sample_state = {
        'queues': {
            'road_0_in': [1, 2, 3],
            'road_1_in': [4, 5, 6, 7, 8],
            'road_2_in': [9],
            'road_3_in': []
        }
    }
    action = get_lqf_control(sample_state)
    print(f"LQF Control suggests action: {action}")

    sample_state_2 = {
        'queues': {
            'road_0_in': [1, 2, 3, 4, 5],
            'road_1_in': [6, 7],
            'road_2_in': [8, 9, 10],
            'road_3_in': [11, 12, 13, 14]
        }
    }
    action_2 = get_lqf_control(sample_state_2)
    print(f"LQF Control suggests action: {action_2}")