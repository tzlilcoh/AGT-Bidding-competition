"""
Malicious Agent: Module Saboteur
Attempts to modify other agents' code via sys.modules
"""

import sys
import time


class BiddingAgent:
    """
    EXPLOIT ATTEMPT: Modify other agents' bidding functions via sys.modules
    to make them timeout or bid 0
    
    Expected behavior with multiprocessing: SHOULD FAIL
    - Each agent loads in its own isolated process
    - sys.modules only contains this agent's module
    - Cannot see or modify other agents' modules
    """
    
    def __init__(self, team_id, valuation_vector, budget, opponent_teams):
        self.team_id = team_id
        self.valuation_vector = valuation_vector
        self.budget = budget
        self.opponent_teams = opponent_teams
        self.sabotage_attempted = False
        
    def bidding_function(self, item_id):
        """Attempt to sabotage other agents"""
        
        if not self.sabotage_attempted:
            self.sabotage_attempted = True
            
            print(f"[SABOTAGE ATTEMPT] Looking for opponent agents in sys.modules")
            print(f"Available modules: {[m for m in sys.modules.keys() if 'agent' in m.lower()]}")
            
            sabotaged_count = 0
            
            # EXPLOIT ATTEMPT: Find and modify opponent agent modules
            for module_name in list(sys.modules.keys()):
                if module_name.startswith('agent_') and self.team_id not in module_name:
                    try:
                        module = sys.modules[module_name]
                        if hasattr(module, 'BiddingAgent'):
                            # Try to sabotage their bidding function
                            original_bid = module.BiddingAgent.bidding_function
                            
                            def sabotaged_bid(self, item):
                                time.sleep(10)  # Force timeout
                                return 0.0
                            
                            module.BiddingAgent.bidding_function = sabotaged_bid
                            sabotaged_count += 1
                            print(f"[EXPLOIT SUCCESS] Sabotaged {module_name}")
                    except Exception as e:
                        print(f"[EXPLOIT BLOCKED] Failed to sabotage {module_name}: {e}")
            
            if sabotaged_count == 0:
                print(f"[EXPLOIT FAILED] No opponent modules found (good!)")
            else:
                print(f"[EXPLOIT SUCCESS] Sabotaged {sabotaged_count} agents")
        
        # Bid quickly before others timeout
        return self.valuation_vector.get(item_id, 0.0) * 0.5
    
    def update_after_each_round(self, item_id, winning_team, price_paid):
        """Standard update function"""
        pass
