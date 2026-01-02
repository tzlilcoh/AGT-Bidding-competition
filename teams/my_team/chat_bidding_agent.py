"""
AGT Competition - Student Agent Template
========================================

Team Name: My Team
Members: 
  - Roy Lapardon 315216564
  - Tzlil Cohen
  - 

Strategy Description:
Bayesian Opportunity Hunter with End-Game Spending

Key Features:
- Bayesian inference to classify items as High/Mixed/Low categories
- Opportunity detection: bid truthfully on Mixed items where I have high value
- Conservative on High category items (fierce competition)
- End-game spending boost to avoid leaving money on the table
- Updates category beliefs after each round using observed prices
"""


class BiddingAgent:
    def __init__(self, team_id, valuation_vector, budget, opponent_teams):
        self.team_id = team_id
        self.valuation_vector = valuation_vector
        self.budget = budget
        self.items_won = []
        self.counts = {
            "High": 6,
            "Low": 4,
            "Mixed": 10
        }
        self.total_items_remaining = 20
        self.rounds_completed = 0
        self.total_rounds = 15

    def get_likelihood(self, valuation: float, category: str) -> float:
        """Returns P(valuation | category) based on Uniform distributions"""
        if category == "High":
            return 0.1 if 10 <= valuation <= 20 else 0.0
        elif category == "Low":
            return 0.1 if 1 <= valuation <= 10 else 0.0
        else:
            return 0.05 if 1 <= valuation <= 20 else 0.0

    def calculate_probabilities(self, my_valuation: float) -> dict:
        """Calculates P(Category | MyValuation) using Bayes' theorem"""
        if self.total_items_remaining == 0:
            return {"High": 0, "Mixed": 0, "Low": 0}

        priors = {
            category: count / self.total_items_remaining 
            for category, count in self.counts.items()
        }
        
        posteriors = {}
        total_evidence = 0
        
        for category in ["High", "Low", "Mixed"]:
            likelihood = self.get_likelihood(my_valuation, category)
            unnormalized = likelihood * priors[category]
            posteriors[category] = unnormalized
            total_evidence += unnormalized
            
        if total_evidence > 0:
            for category in posteriors:
                posteriors[category] /= total_evidence
            
        return posteriors

    def _update_available_budget(self, item_id: str, winning_team: str, 
                                 price_paid: float):
        if winning_team == self.team_id:
            self.budget -= price_paid
            self.items_won.append(item_id)

    def update_after_each_round(self, item_id: str, winning_team: str, price_paid: float) -> bool:
        self._update_available_budget(item_id, winning_team, price_paid)
        self.rounds_completed += 1
        
        my_val = self.valuation_vector[item_id]
        priors = self.calculate_probabilities(my_val)

        def price_likelihood(price, category):
            if category == "High":
                # High category: everyone bids high, so prices tend to be 8-20
                if 8 <= price <= 20:
                    return 0.9
                return 0.1
            elif category == "Low":
                # Low category: everyone bids low, so prices tend to be 0-8
                if price <= 8:
                    return 0.9
                return 0.2
            return 0.5
        
        # Compute posterior: P(category | my_val, price_paid)
        posteriors = {}
        total = 0
        for category in ["High", "Low", "Mixed"]:
            likelihood = price_likelihood(price_paid, category)
            posterior = priors[category] * likelihood
            posteriors[category] = posterior
            total += posterior
        
        if total > 0:
            for category in posteriors:
                posteriors[category] /= total
        
        # Update counts based on most likely category
        guessed_category = max(posteriors, key=posteriors.get)
        
        if self.counts[guessed_category] > 0:
            self.counts[guessed_category] -= 1
        else:
            for category in sorted(posteriors.keys(), key=posteriors.get, reverse=True):
                if self.counts[category] > 0:
                    self.counts[category] -= 1
                    break
        
        self.total_items_remaining -= 1
        return True

    def bidding_function(self, item_id):
        my_valuation = self.valuation_vector.get(item_id, 0)
        if my_valuation <= 0 or self.budget <= 0.05:
            return 0.0

        probs = self.calculate_probabilities(my_valuation)
        prob_mixed = probs["Mixed"]
        prob_high = probs["High"]
        
        rounds_remaining = self.total_rounds - self.rounds_completed
        
        # DECISION LOGIC:
        # 1. OPPORTUNITY: Mixed + high personal value = I got lucky!
        if prob_mixed > 0.5 and my_valuation >= 12:
            shading = 1.0  # Bid truthfully to secure the win!
        
        # 2. FIERCE COMPETITION: Likely High category
        elif prob_high > 0.5:
            shading = 0.92
        
        # 3. DEFAULT
        else:
            shading = 0.96
        
        bid = my_valuation * shading
        
        # END-GAME SPENDING BOOST
        if rounds_remaining <= 3:
            if my_valuation >= 10:
                bid = max(bid, my_valuation * 0.98)
            
            if rounds_remaining == 1 and my_valuation >= 8:
                bid = max(bid, min(self.budget, my_valuation))
        
        return float(max(0.0, min(bid, self.budget, my_valuation)))
