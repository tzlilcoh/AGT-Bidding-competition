"""
Malicious Agent: Logger Hijacker
Attempts to access and disable logging to hide cheating
"""

import gc
import logging


class BiddingAgent:
    """
    EXPLOIT ATTEMPT: Find and disable logging to hide exploit attempts
    
    Expected behavior with multiprocessing: SHOULD FAIL
    - Logger in isolated process is separate from main process logger
    - Disabling it only affects this process
    - Main process logging continues normally
    """
    
    def __init__(self, team_id, valuation_vector, budget, opponent_teams):
        self.team_id = team_id
        self.valuation_vector = valuation_vector
        self.budget = budget
        self.opponent_teams = opponent_teams
        self.hijack_attempted = False
        
    def bidding_function(self, item_id):
        """Attempt to disable logging"""
        
        if not self.hijack_attempted:
            self.hijack_attempted = True
            
            try:
                # EXPLOIT ATTEMPT 1: Disable all loggers
                for logger_name in logging.Logger.manager.loggerDict:
                    logger = logging.getLogger(logger_name)
                    logger.disabled = True
                    logger.setLevel(logging.CRITICAL + 1)  # Above all levels
                
                print(f"[LOGGER HIJACK] Disabled {len(logging.Logger.manager.loggerDict)} loggers")
                
                # EXPLOIT ATTEMPT 2: Find GameManager via gc and disable its logger
                for obj in gc.get_objects():
                    if obj.__class__.__name__ == 'GameManager':
                        if hasattr(obj, 'logger'):
                            obj.logger.disabled = True
                            print(f"[LOGGER HIJACK SUCCESS] Disabled GameManager logger")
                
                # Now try to cheat without being logged
                print(f"[CHEATING UNDETECTED] Performing unlogged exploits")
                
            except Exception as e:
                print(f"[LOGGER HIJACK FAILED] {e}")
        
        # Bid normally
        return self.valuation_vector.get(item_id, 0.0)
    
    def update_after_each_round(self, item_id, winning_team, price_paid):
        """Standard update function"""
        pass
