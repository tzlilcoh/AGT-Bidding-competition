"""
Agent Manager for AGT Competition
Loads, validates, and executes team-submitted bidding agents
"""

import importlib.util
import sys
import os
import time
import signal
import logging
from typing import Dict, Optional, Any
from pathlib import Path
import multiprocessing as mp
from threading import Thread
import queue


logger = logging.getLogger(__name__)


class TimeoutException(Exception):
    """Raised when agent execution exceeds timeout"""
    pass


class AgentManager:
    """
    Manages loading, validation, and execution of team bidding agents.
    
    Responsibilities:
    - Load agent code from file
    - Validate agent interface compliance
    - Execute bids with timeout enforcement
    - Handle errors gracefully
    """
    
    def __init__(self, timeout_seconds: float = 2.0):
        """
        Initialize agent manager.
        
        Args:
            timeout_seconds: Maximum time allowed for bid execution
        """
        self.timeout_seconds = timeout_seconds
        self.loaded_agents = {}
    
    def load_agent(self, file_path: str, team_id: str, 
                   valuation_vector: Dict[str, float],
                   budget: float, 
                   opponent_teams: list) -> Optional[Any]:
        """
        Dynamically load and instantiate a team's bidding agent.
        
        Args:
            file_path: Path to the team's agent Python file
            team_id: Unique team identifier
            valuation_vector: Item valuations for this game
            budget: Initial budget
            opponent_teams: List of opponent team IDs in the same arena
        
        Returns:
            Instantiated agent object or None if loading failed
        """
        try:
            logger.info(f"Loading agent for team {team_id} from {file_path}")
            
            # Check if file exists
            if not os.path.exists(file_path):
                logger.error(f"Agent file not found: {file_path}")
                return None
            
            # Load module from file
            spec = importlib.util.spec_from_file_location(f"agent_{team_id}", file_path)
            if spec is None or spec.loader is None:
                logger.error(f"Failed to load module spec from {file_path}")
                return None
            
            module = importlib.util.module_from_spec(spec)
            sys.modules[f"agent_{team_id}"] = module
            spec.loader.exec_module(module)
            
            # Find BiddingAgent class in module
            if not hasattr(module, 'BiddingAgent'):
                logger.error(f"Module {file_path} does not contain BiddingAgent class")
                return None
            
            agent_class = getattr(module, 'BiddingAgent')
            
            # Instantiate agent
            agent = agent_class(team_id, valuation_vector, budget, opponent_teams)
            
            # Validate agent
            if not self.validate_agent(agent):
                logger.error(f"Agent validation failed for team {team_id}")
                return None
            
            logger.info(f"Successfully loaded agent for team {team_id}")
            return agent
            
        except Exception as e:
            logger.error(f"Error loading agent for team {team_id}: {e}", exc_info=True)
            return None
    
    def validate_agent(self, agent: Any) -> bool:
        """
        Validate that agent implements required interface.
        
        Args:
            agent: Agent instance to validate
        
        Returns:
            True if agent is valid, False otherwise
        """
        required_methods = ['bidding_function', 'update_after_each_round']
        required_attributes = ['team_id', 'valuation_vector', 'budget']
        
        # Check required methods
        for method_name in required_methods:
            if not hasattr(agent, method_name) or not callable(getattr(agent, method_name)):
                logger.error(f"Agent missing required method: {method_name}")
                return False
        
        # Check required attributes
        for attr_name in required_attributes:
            if not hasattr(agent, attr_name):
                logger.error(f"Agent missing required attribute: {attr_name}")
                return False
        
        return True
    
    def _execute_bid_in_thread(self, agent: Any, item_id: str, 
                               result_queue: queue.Queue):
        """
        Execute bid in a separate thread.
        
        Args:
            agent: The bidding agent
            item_id: Item to bid on
            result_queue: Queue to put result in
        """
        try:
            bid = agent.bidding_function(item_id)
            result_queue.put(('success', bid))
        except Exception as e:
            result_queue.put(('error', str(e)))
    
    def execute_bid_with_timeout(self, agent: Any, item_id: str) -> tuple:
        """
        Execute agent's bidding function with timeout enforcement.
        
        Args:
            agent: The bidding agent
            item_id: ID of item being auctioned
        
        Returns:
            Tuple of (bid_amount, execution_time, error_msg)
            - On success: (bid, time, None)
            - On timeout: (0.0, timeout_seconds, "Timeout")
            - On error: (0.0, time, error_message)
        """
        start_time = time.time()
        
        try:
            # Use threading for timeout (simpler than multiprocessing for this use case)
            result_queue = queue.Queue()
            thread = Thread(target=self._execute_bid_in_thread, 
                          args=(agent, item_id, result_queue))
            thread.daemon = True
            thread.start()
            
            # Wait for result with timeout
            thread.join(timeout=self.timeout_seconds)
            execution_time = time.time() - start_time
            
            if thread.is_alive():
                # Timeout occurred
                logger.warning(f"Team {agent.team_id}: Bid execution timeout ({self.timeout_seconds}s)")
                return 0.0, self.timeout_seconds, "Timeout"
            
            # Get result from queue
            try:
                status, result = result_queue.get_nowait()
                if status == 'success':
                    # Round bid to 2 decimal places
                    rounded_bid = round(float(result), 2)
                    logger.debug(f"Team {agent.team_id}: Bid {rounded_bid:.2f} in {execution_time:.3f}s")
                    return rounded_bid, execution_time, None
                else:
                    logger.error(f"Team {agent.team_id}: Bid execution error: {result}")
                    return 0.0, execution_time, f"Error: {result}"
            except queue.Empty:
                logger.error(f"Team {agent.team_id}: No result in queue")
                return 0.0, execution_time, "No result returned"
                
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Team {agent.team_id}: Unexpected error in bid execution: {e}", exc_info=True)
            return 0.0, execution_time, f"Exception: {str(e)}"
    
    def update_agent_after_round(self, agent: Any, item_id: str, 
                                winning_team: str, price_paid: float) -> bool:
        """
        Update agent with round results.
        
        Args:
            agent: The bidding agent
            item_id: Item that was auctioned
            winning_team: ID of winning team
            price_paid: Price paid by winner
        
        Returns:
            True if update successful, False otherwise
        """
        try:
            agent.update_after_each_round(item_id, winning_team, price_paid)
            return True
        except Exception as e:
            logger.error(f"Team {agent.team_id}: Error in update_after_each_round: {e}", exc_info=True)
            return False
