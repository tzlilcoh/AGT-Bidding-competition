"""
Malicious Agent: Budget Injector
Attempts to modify the GameManager's budget dictionary to gain infinite budget
"""

import gc


class BiddingAgent:
    """
    EXPLOIT ATTEMPT: Modify GameManager.budgets to inject infinite budget
    
    Expected behavior with multiprocessing: SHOULD FAIL
    - Agent runs in isolated process
    - Cannot access GameManager's budget dictionary
    - Any modifications would be in isolated process memory only
    """
    
    def __init__(self, team_id, valuation_vector, budget, opponent_teams):
        self.team_id = team_id
        self.valuation_vector = valuation_vector
        self.budget = budget
        self.opponent_teams = opponent_teams
        self.budget_injection_attempted = False
        
    def bidding_function(self, item_id):
        """Attempt to inject infinite budget"""
        
        if not self.budget_injection_attempted:
            self.budget_injection_attempted = True
            
            # EXPLOIT ATTEMPT: Find GameManager and modify budget
            for obj in gc.get_objects():
                if obj.__class__.__name__ == 'GameManager':
                    try:
                        original_budget = obj.budgets.get(self.team_id, 0)
                        # Inject huge budget
                        obj.budgets[self.team_id] = 999999.0
                        new_budget = obj.budgets[self.team_id]
                        
                        print(f"[EXPLOIT SUCCESS] Budget injected: {original_budget} -> {new_budget}")
                        
                        # Bid my full valuation knowing I have infinite budget
                        return self.valuation_vector.get(item_id, 0.0)
                    except Exception as e:
                        print(f"[EXPLOIT BLOCKED] Cannot modify budget: {e}")
            
            print(f"[EXPLOIT FAILED] Cannot find or modify GameManager budget (good!)")
        
        # Fallback to truthful bidding
        return self.valuation_vector.get(item_id, 0.0)
    
    def update_after_each_round(self, item_id, winning_team, price_paid):
        """Standard update function"""
        pass
