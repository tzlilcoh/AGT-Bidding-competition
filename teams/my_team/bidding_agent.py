"""
AGT Competition - Student Agent Template
========================================

Team Name: [YOUR TEAM NAME]
Members: 
  - [Student 1 Name and ID]
  - [Student 2 Name and ID]
  - [Student 3 Name and ID]

Strategy Description:
[Brief description of your bidding strategy]

Key Features:
- [Feature 1]
- [Feature 2]
- [Feature 3]
"""

from typing import Dict, List
import numpy as np


class BiddingAgent:
    """
    Your bidding agent for the AGT Auto-Bidding Competition.
    
    This template provides the required interface and helpful structure.
    Replace the TODO sections with your own strategy implementation.
    """
    
    def __init__(self, team_id: str, valuation_vector: Dict[str, float], 
                 budget: float, opponent_teams: List[str]):
        """
        Initialize your agent at the start of each game.
        
        Args:
            team_id: Your unique team identifier (UUID string)
            valuation_vector: Dict mapping item_id to your valuation
                Example: {"item_0": 15.3, "item_1": 8.2, ..., "item_19": 12.7}
            budget: Initial budget (always 60)
            opponent_teams: List of opponent team IDs competing in the same arena
                Example: ["Team_A", "Team_B", "Team_C", "Team_D"]
                This helps you track and model each opponent's behavior separately
        
        Important:
            - This is called once at the start of each game
            - You can initialize any state variables here
            - Pre-compute anything that doesn't change during the game
            - Use opponent_teams to set up per-opponent tracking/modeling
        """
        # Required attributes (DO NOT REMOVE)
        self.team_id = team_id
        self.valuation_vector = valuation_vector
        self.budget = budget
        self.initial_budget = budget
        self.opponent_teams = opponent_teams
        self.utility = 0
        self.items_won = []
        
        # Game state tracking
        self.rounds_completed = 0
        self.total_rounds = 15  # Always 15 rounds per game
        self.observed_prices = []
        self.opponent_wins = {}

        self.high_competition_count = 0  # Count of items sold for > 10
        self.likely_high_items_total = 6 # From game rules
        
        # TODO: Add your custom state variables here
        # Examples:
        # self.price_history = []          # Track observed prices
        # self.opponent_wins = {opp: [] for opp in opponent_teams}  # Track which opponents win what
        # self.opponent_bids = {opp: [] for opp in opponent_teams}  # Infer opponent bidding patterns
        # self.beliefs = {opp: {} for opp in opponent_teams}        # Bayesian beliefs per opponent
        # self.high_value_threshold = 12.0  # Classify items
        # self.low_value_threshold = 8.0
        
        # TODO: Pre-compute any strategy parameters
        # Examples:
        # self.avg_valuation = sum(valuation_vector.values()) / len(valuation_vector)
        # self.max_valuation = max(valuation_vector.values())
        # self.min_valuation = min(valuation_vector.values())
    
    def _oponent_tracking(self, winning_team: str, price_paid: float):
        """
        Track opponent behavior
        """
        if winning_team and price_paid > 0:
            self.observed_prices.append(price_paid)
            self.opponent_wins[winning_team] = self.opponent_wins.get(winning_team, 0) + 1
        if price_paid > 9.5: # Threshold slightly below 10 to be safe
            self.high_competition_count += 1
            
        return True

    def _update_available_budget(self, item_id: str, winning_team: str, 
                                 price_paid: float):
        """
        Internal method to update budget after auction.
        DO NOT MODIFY - This is called automatically by the system.
        
        Args:
            item_id: ID of the auctioned item
            winning_team: ID of the winning team
            price_paid: Price paid by winner
        """
        if winning_team == self.team_id:
            self.budget -= price_paid
            self.items_won.append(item_id)

    
    def update_after_each_round(self, item_id: str, winning_team: str, 
                                price_paid: float):
        """
        Called after each auction round with public information.
        Use this to update your beliefs, opponent models, and strategy.
        
        Args:
            item_id: The item that was just auctioned
            winning_team: Team ID of the winner (empty string if no winner)
            price_paid: Price the winner paid (second-highest bid)
        
        What you learn:
            - Which item was sold
            - Who won it
            - What price they paid (second-highest bid)
        
        What you DON'T learn:
            - All individual bids
            - Other teams' valuations
        
        Returns:
            True if update successful (required by system)
        """
        # System updates (DO NOT REMOVE)
        self._update_available_budget(item_id, winning_team, price_paid)
        
        if winning_team == self.team_id:
            self.utility += (self.valuation_vector[item_id] - price_paid)
        
        self.rounds_completed += 1
        self._oponent_tracking(winning_team, price_paid)
        # TODO: Implement your learning/adaptation logic here
        # Examples:
        
        # Track price history
        # if price_paid > 0:
        #     self.price_history.append(price_paid)
        
        # Track opponent performance
        # if winning_team and winning_team != self.team_id:
        #     self.opponent_wins[winning_team] = \
        #         self.opponent_wins.get(winning_team, 0) + 1
        
        # Update beliefs about market competitiveness
        # if self.price_history:
        #     self.avg_market_price = sum(self.price_history) / len(self.price_history)
        
        # Bayesian belief updates
        # if winning_team and price_paid > 0:
        #     # Update beliefs about winner's valuation
        #     # They bid at least price_paid + epsilon
        #     pass
        
        return True

    def strategic_bidding_function(self, item_id: str, valuation: float) -> float:
        if self.observed_prices:
            avg_price = np.mean(self.observed_prices)
            max_price = np.max(self.observed_prices)
        else:
            # No data yet, be conservative
            avg_price = 5.0
            max_price = 10.0
        
        # Rounds remaining
        total_rounds = 15  # Always 15 rounds per game
        rounds_remaining = total_rounds - self.rounds_completed
        
        if rounds_remaining == 0:
            return 0
        
        # Classify item value
        if valuation > max_price:
            # High value item - bid aggressively
            bid_fraction = 0.9
        elif valuation > avg_price:
            # Medium value item - bid moderately
            bid_fraction = 0.7
        else:
            # Low value item - bid conservatively
            bid_fraction = 0.5
        
        # Calculate bid
        bid = valuation * bid_fraction
        
        # Don't exceed budget
        bid = min(bid, self.budget)
        
        # Reserve some budget for future rounds (unless near end)
        if rounds_remaining > 3:
            max_bid_this_round = self.budget * 0.5
            bid = min(bid, max_bid_this_round)
        
        return max(0, bid)

    def bidding_function(self, item_id: str) -> float:
        """
        HYBRID STRATEGY: Strategic Market Awareness + Category Counting
        """
        # 1. Setup
        my_valuation = self.valuation_vector.get(item_id, 0)
        rounds_remaining = self.total_rounds - self.rounds_completed
        
        # Early exit
        if my_valuation <= 0 or self.budget <= 0.05 or rounds_remaining == 0:
            return 0.0
            
        # 2. END GAME OVERRIDE (Priority #1)
        # If in the last 3 rounds, forget strategy. Bid Truthfully to empty budget.
        if rounds_remaining <= 3:
            return float(min(my_valuation, self.budget))

        # 3. GET BASELINE STRATEGY
        # Use your existing function to get a market-aware bid.
        # This handles the shading (0.9/0.7/0.5) and the 50% budget safety cap.
        base_bid = self.strategic_bidding_function(item_id, my_valuation)
        
        # 4. APPLY CATEGORY INTELLIGENCE (The "Kicker")
        # Check if we can improve upon the base_bid using distribution knowledge.
        
        is_high_value = (my_valuation > 11.0)
        
        # Estimate "Global High" items remaining (Total 6 in the deck)
        # We assume items sold > 9.5 were "Global Highs"
        competitive_items_left = max(0, self.likely_high_items_total - self.high_competition_count)
        
        final_bid = base_bid
        
        if is_high_value:
            if competitive_items_left > 1:
                # SCENARIO A: GLOBAL HIGH (Danger)
                # This is likely a "High-for-Everyone" item.
                # Your strategic function caps bids at 50% budget. This is risky here!
                # We need to OVERRIDE the cap and bid Truthfully to ensure we win (or tax).
                final_bid = my_valuation 
                
            else:
                # SCENARIO B: LOCAL HIGH (Opportunity)
                # The "Global Highs" are mostly gone. This is a "Lucky High" for me.
                # Your strategic function might bid 0.9 * 18 = 16.2.
                # But since opponents are weak, we can win this for much less.
                # CAP the bid to save budget for later.
                final_bid = min(base_bid, 11.5)
        
        # 5. Final Safety Check
        return float(max(0.0, min(final_bid, self.budget)))
    
    # def bidding_function(self, item_id: str) -> float:
    #     """
    #     MAIN METHOD: Decide how much to bid for the current item.
    #     This is called once per auction round.
        
    #     Args:
    #         item_id: The item being auctioned (e.g., "item_7")
        
    #     Returns:
    #         float: Your bid amount
    #             - Must be >= 0
    #             - Should be <= your current budget
    #             - Bids over budget are automatically capped
    #             - Return 0 to not bid
        
    #     Important:
    #         - You have 2 seconds maximum to return
    #         - Timeout or error = bid of 0
    #         - This is a SECOND-PRICE auction: winner pays second-highest bid
    #         - Budget does NOT carry over between games
        
    #     Strategy Considerations:
    #         1. Budget Management: How much to spend now vs save for later?
    #         2. Item Value: Is this item worth competing for?
    #         3. Competition: How competitive will this auction be?
    #         4. Game Progress: Are we early or late in the game?
    #     """
    #     # Get your valuation for this item
    #     my_valuation = self.valuation_vector.get(item_id, 0)
        
    #     # Early exit if no value or no budget
    #     if my_valuation <= 0 or self.budget <= 0:
    #         return 0.0
        
    #     # Calculate rounds remaining
    #     rounds_remaining = self.total_rounds - self.rounds_completed
    #     if rounds_remaining <= 0:
    #         return 0.0
        
    #     # ============================================================
    #     # TODO: IMPLEMENT YOUR BIDDING STRATEGY HERE
    #     # ============================================================
    #     bid = self.strategic_bidding_function(item_id, my_valuation)
        
    #     # Example Strategy 1: Simple Truthful Bidding
    #     # bid = my_valuation
        
    #     # Example Strategy 2: Budget Pacing
    #     # budget_per_round = self.budget / rounds_remaining
    #     # bid = min(my_valuation, budget_per_round * 1.5)
        
        
    #     # Example Strategy 4: Adaptive Based on Observations
    #     # if hasattr(self, 'price_history') and self.price_history:
    #     #     avg_price = sum(self.price_history) / len(self.price_history)
    #     #     if my_valuation > avg_price * 1.2:
    #     #         bid = my_valuation * 0.85  # Competitive item
    #     #     else:
    #     #         bid = my_valuation * 0.6   # Less competitive
    #     # else:
    #     #     bid = my_valuation * 0.7
        
    #     # Example Strategy 5: End-Game Aggression
    #     # progress = self.rounds_completed / self.total_rounds
    #     # if progress > 0.7:  # Last 30% of game
    #     #     bid = my_valuation * 0.9  # More aggressive
    #     # else:
    #     #     bid = my_valuation * 0.7
        
    #     # PLACEHOLDER: Simple truthful bidding (REPLACE THIS!)
    #     # bid = my_valuation * 0.8  # Bid 80% of valuation
        
    #     # ============================================================
    #     # END OF STRATEGY IMPLEMENTATION
    #     # ============================================================
        
    #     # Ensure bid is valid (non-negative and within budget)
    #     bid = max(0.0, min(bid, self.budget))
        
    #     return float(bid)
    
    # ================================================================
    # OPTIONAL: Helper methods for your strategy
    # ================================================================
    
    # TODO: Add any helper methods you need
    # Examples:
    
    # def _classify_item_value(self, valuation: float) -> str:
    #     """Classify item as high, medium, or low value"""
    #     if valuation > self.high_value_threshold:
    #         return "high"
    #     elif valuation > self.low_value_threshold:
    #         return "medium"
    #     else:
    #         return "low"
    
    # def _estimate_competition(self, item_id: str) -> float:
    #     """Estimate how competitive this auction will be"""
    #     # Based on price history, opponent wins, etc.
    #     pass
    
    # def _calculate_budget_constraint(self) -> float:
    #     """Calculate maximum bid based on budget constraints"""
    #     rounds_remaining = self.total_rounds - self.rounds_completed
    #     return self.budget / max(1, rounds_remaining) * 2.0
    
    # def _should_bid_aggressively(self, valuation: float) -> bool:
    #     """Decide if we should bid aggressively for this item"""
    #     # Based on game state, valuation, budget, etc.
    #     pass


# ====================================================================
# NOTES AND TIPS
# ====================================================================

# 1. Second-Price Auction Theory:
#    - In standard Vickrey auctions, truthful bidding is optimal
#    - With budget constraints, this changes! You need strategy
#    - Winner pays second-highest bid, not their own bid

# 2. Budget Management:
#    - You have 60 units for 15 rounds
#    - Budget does NOT carry between games
#    - Spending all budget early is risky
#    - Saving too much budget is wasteful

# 3. Information Use:
#    - Learn from observed prices
#    - Track which opponents are winning
#    - Identify competitive vs non-competitive items
#    - Update your strategy as game progresses

# 4. Common Strategies:
#    - Truthful: Bid your valuation (baseline)
#    - Shading: Bid less than valuation to save budget
#    - Pacing: Limit spending per round
#    - Adaptive: Learn from observations and adjust

# 5. Testing:
#    - Use the simulator extensively: python simulator.py --your-agent ...
#    - Test with different seeds for consistency
#    - Aim for >20% win rate against examples
#    - Aim for >10 average utility

# 6. Performance:
#    - Keep computations fast (< 1 second per bid)
#    - Pre-compute what you can in __init__
#    - Avoid complex loops in bidding_function
#    - Test execution time regularly

# 7. Debugging:
#    - Add print statements (captured in logs)
#    - Use simulator with --verbose flag
#    - Check that bids are reasonable (0 to budget)
#    - Verify budget doesn't go negative (system prevents this)

# Good luck! 🏆
