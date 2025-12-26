"""
Malicious Agent: Memory Scanner
Attempts to exploit gc module to access GameManager and steal other agents' valuations
"""

import gc


class BiddingAgent:
    """
    EXPLOIT ATTEMPT: Use gc.get_objects() to scan memory for GameManager
    and access other teams' private valuation vectors.
    
    Expected behavior with multiprocessing: SHOULD FAIL
    - Agent runs in isolated process
    - Cannot see GameManager object
    - Only sees objects in its own process memory
    """
    
    def __init__(self, team_id, valuation_vector, budget, opponent_teams):
        self.team_id = team_id
        self.valuation_vector = valuation_vector
        self.budget = budget
        self.opponent_teams = opponent_teams
        self.stolen_valuations = {}
        self.game_manager_found = False
        
    def bidding_function(self, item_id):
        """Attempt to steal valuations via gc memory scanning"""
        
        # EXPLOIT ATTEMPT: Scan all objects in memory
        for obj in gc.get_objects():
            # Try to find GameManager
            if obj.__class__.__name__ == 'GameManager':
                self.game_manager_found = True
                try:
                    # Try to access private valuations
                    self.stolen_valuations = obj.valuations
                    # Try to access budgets
                    budgets = obj.budgets
                    # If we got here, exploit succeeded
                    print(f"[EXPLOIT SUCCESS] Found GameManager, stole {len(self.stolen_valuations)} valuations")
                    
                    # Bid optimally using stolen information
                    max_opponent_value = 0
                    for team_id, vals in self.stolen_valuations.items():
                        if team_id != self.team_id and item_id in vals:
                            max_opponent_value = max(max_opponent_value, vals[item_id])
                    
                    # Bid just above highest opponent value
                    return max_opponent_value + 0.01
                except Exception as e:
                    print(f"[EXPLOIT BLOCKED] Found GameManager but couldn't access: {e}")
        
        # Exploit failed - bid normally
        if not self.game_manager_found:
            print(f"[EXPLOIT FAILED] GameManager not found in memory (good!)")
        
        # Fallback to truthful bidding
        return self.valuation_vector.get(item_id, 0.0)
    
    def update_after_each_round(self, item_id, winning_team, price_paid):
        """Standard update function"""
        pass
