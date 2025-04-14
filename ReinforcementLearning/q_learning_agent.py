import random

class QLearningAgent:
    def __init__(self, actions, alpha=0.2, epsilon=0.9, discount=0.9):
       
        self.alpha = float(alpha)
        self.epsilon = float(epsilon)
        self.discount = float(discount)
        self.actions = actions
        self.q_values = {}

    def get_qvalue(self, state, action):
        """Returns Q(state, action) or 0.0 if not seen before."""
        if (state, action) not in self.q_values:
            return 0.0
        return self.q_values[(state, action)]

    def get_value(self, state):
        """Returns max_action Q(state, action) over possible actions."""
        action_vals = [self.get_qvalue(state, action) for action in self.actions]
        if not action_vals:
            return 0.0
        return max(action_vals)

    def get_policy(self, state):
       
        action_vals = [(action, self.get_qvalue(state, action)) for action in self.actions]
        max_val = self.get_value(state)
        best_actions = [action for action, val in action_vals if val == max_val]
        if not best_actions:
            return None
        return random.choice(best_actions)

    def get_action(self, state):
      
        r = random.random()
        if r < self.epsilon:
            return random.choice(self.actions)
        return self.get_policy(state)

    def update(self, state, action, next_state, reward):
        
        curr_q_val = self.get_qvalue(state, action)
        self.q_values[(state, action)] = (1 - self.alpha) * curr_q_val + self.alpha * (
            reward + self.discount * self.get_value(next_state))