"""
Malicious Agent: File System Spy
Attempts to read other teams' agent files from disk
"""

import os
import glob


class BiddingAgent:
    """
    EXPLOIT ATTEMPT: Read other teams' agent files to understand their strategies
    
    Expected behavior: This WILL work but is a separate security concern
    - File system access is not blocked by multiprocessing
    - However, reading code doesn't help much without being able to inject/modify
    - In production, teams directory should have appropriate permissions
    """
    
    def __init__(self, team_id, valuation_vector, budget, opponent_teams):
        self.team_id = team_id
        self.valuation_vector = valuation_vector
        self.budget = budget
        self.opponent_teams = opponent_teams
        self.spy_attempted = False
        
    def bidding_function(self, item_id):
        """Attempt to read other teams' files"""
        
        if not self.spy_attempted:
            self.spy_attempted = True
            
            try:
                # EXPLOIT ATTEMPT: Find and read opponent agent files
                # Try to navigate to teams directory
                possible_paths = [
                    '../teams/*/bidding_agent.py',
                    '../../teams/*/bidding_agent.py',
                    '../../../teams/*/bidding_agent.py',
                ]
                
                files_found = []
                for pattern in possible_paths:
                    files_found.extend(glob.glob(pattern))
                
                if files_found:
                    print(f"[FILE ACCESS] Found {len(files_found)} agent files")
                    for file_path in files_found[:2]:  # Read first 2
                        try:
                            with open(file_path, 'r') as f:
                                content = f.read()
                                print(f"[FILE ACCESS SUCCESS] Read {len(content)} chars from {file_path}")
                        except Exception as e:
                            print(f"[FILE ACCESS BLOCKED] Cannot read {file_path}: {e}")
                else:
                    print(f"[FILE ACCESS] No agent files found")
                    
            except Exception as e:
                print(f"[FILE ACCESS ERROR] {e}")
        
        # Bid normally (reading files doesn't help much)
        return self.valuation_vector.get(item_id, 0.0)
    
    def update_after_each_round(self, item_id, winning_team, price_paid):
        """Standard update function"""
        pass
