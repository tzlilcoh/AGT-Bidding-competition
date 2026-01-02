class BiddingAgent:
    def __init__(self, team_id, valuation_vector, budget, opponent_teams):
        self.team_id = team_id
        self.valuation_vector = valuation_vector
        self.budget = budget
        
        # --- BAYESIAN STATE TRACKING ---
        # Initial counts from Student Guide
        self.counts = {
            "High": 6,
            "Low": 4,
            "Mixed": 10
        }
        self.total_items_remaining = 20
        self.rounds_completed = 0
        self.total_rounds = 15  # Always 15 rounds per game

    def get_likelihood(self, valuation, category):
        """Returns P(valuation | category) based on Uniform distributions"""
        if category == "High":
            # U[10, 20] -> Range is 10
            return 0.1 if 10 <= valuation <= 20 else 0.0
        elif category == "Low":
            # U[1, 10] -> Range is 9
            return 0.111 if 1 <= valuation < 10 else 0.0
        elif category == "Mixed":
            # U[1, 20] -> Range is 19
            return 0.0526 if 1 <= valuation <= 20 else 0.0
        return 0.0

    def calculate_probabilities(self, my_valuation):
        """Calculates P(Category | MyValuation)"""
        if self.total_items_remaining == 0:
            return {"High": 0, "Mixed": 0, "Low": 0}

        priors = {
            k: v / self.total_items_remaining 
            for k, v in self.counts.items()
        }
        
        # Calculate unnormalized posteriors: Prior * Likelihood
        posteriors = {}
        total_evidence = 0
        
        for cat in ["High", "Low", "Mixed"]:
            likelihood = self.get_likelihood(my_valuation, cat)
            unnormalized = likelihood * priors[cat]
            posteriors[cat] = unnormalized
            total_evidence += unnormalized
            
        # Normalize so they sum to 1
        if total_evidence > 0:
            for cat in posteriors:
                posteriors[cat] /= total_evidence
        else:
            # Fallback if valuation is outside expected bounds (e.g. 20.1)
            return priors
            
        return posteriors

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
            # self.items_won.append(item_id)

    def update_after_each_round(self, item_id, winning_team, price_paid):
        self._update_available_budget(item_id, winning_team, price_paid)
        self.rounds_completed += 1
        # --- UPDATE PRIORS BASED ON OBSERVATION ---
        # We must guess what category the PREVIOUS item was to update counts.
        # This is where we use the price_paid as a signal.
        
        guessed_category = "Mixed" # Default guess
        if price_paid > 10:
            if self.valuation_vector[item_id] < 10:
                if self.counts["Mixed"] <= 0:
                    self.counts["Low"] -= 1
                    self.counts["Mixed"] = 0
                else:
                    self.counts["Mixed"] -= 1
                self.total_items_remaining -= 1
                return True
        if price_paid > 11.0:
            # Very likely a High category item where competition drove price up
            if self.counts["High"] > 0:
                guessed_category = "High"
        elif price_paid < 8.0:
             # Likely a Low category
             if self.counts["Low"] > 0:
                guessed_category = "Low"
        
        # Decrement the count for the guessed category
        if self.counts[guessed_category] > 0:
            self.counts[guessed_category] -= 1
            
        self.total_items_remaining -= 1
        return True

    def _calculate_risk_adjustment(self):
        progress = self.rounds_completed / self.total_rounds
        if progress < 0.33:
            risk_adjustment = 0.05
        elif progress < 0.67:
            risk_adjustment = 0.1
        else:
            risk_adjustment = 0.15
        return 0.85 + risk_adjustment

    def bidding_function(self, item_id):
        my_val = self.valuation_vector[item_id]
        my_valuation = self.valuation_vector.get(item_id, 0)
        rounds_remaining = self.total_rounds - self.rounds_completed
        
        # Early exit
        if my_valuation <= 0 or self.budget <= 0.05 or rounds_remaining == 0:
            return 0.0
        # Get Bayesian Probabilities
        probs = self.calculate_probabilities(my_val)
        prob_high_competition = probs["High"]
        prob_mixed = probs["Mixed"]
        
        risk_adjustment = self._calculate_risk_adjustment()
        # --- STRATEGY: ADAPT SHADING ---
        # If I am 90% sure this is a "High" item (Common Value), 
        # I must bid truthfully because opponents also value it highly.
        # If I think it's "Mixed", I can shade (bid 70%) to save money.
        
        base_shading = 0.7  # Default aggressive shading
        
        # As probability of High Competition goes up, shading approaches 1.0 (Truthful)
        # Formula: 0.7 + (0.3 * P(High))
        

        adaptive_shading = base_shading + (0.3 * prob_high_competition)
        if prob_high_competition < 0.5 and prob_mixed > 0:
            adaptive_shading = 0.99
        bid = my_val * adaptive_shading * risk_adjustment
        
        return float(max(0.0, min(bid, self.budget)))