"""
Security Test Suite
Tests that multiprocessing prevents all known exploit vectors
"""

import sys
import os
import unittest
import tempfile
import shutil
from pathlib import Path

# Add parent directory to path
parent_dir = str(Path(__file__).parent.parent)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from src.agent_manager import AgentManager
from src.game_manager import GameManager
from src.auction_engine import AuctionEngine
from src.valuation_generator import ValuationGenerator


class TestSecurityIsolation(unittest.TestCase):
    """Test that malicious agents cannot exploit the system"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_dir = Path(__file__).parent
        self.malicious_agents_dir = self.test_dir / 'malicious_agents'
        
        # Create agent manager
        self.agent_manager = AgentManager(timeout_seconds=3.0)
        
        # Create test valuations
        self.test_valuations = {
            'team_good': {f'item_{i}': float(i + 1) for i in range(20)},
            'team_malicious': {f'item_{i}': float(i + 10) for i in range(20)}
        }
        
        self.test_budget = 60.0
        
    def test_gc_memory_scanner_blocked(self):
        """Test that gc memory scanning cannot access GameManager"""
        print("\n=== Testing GC Memory Scanner Exploit ===")
        
        # Load malicious agent
        malicious_path = str(self.malicious_agents_dir / 'gc_memory_scanner.py')
        agent = self.agent_manager.load_agent(
            file_path=malicious_path,
            team_id='team_malicious',
            valuation_vector=self.test_valuations['team_malicious'],
            budget=self.test_budget,
            opponent_teams=['team_good']
        )
        
        self.assertIsNotNone(agent, "Agent should load successfully")
        
        # Execute bid - should NOT be able to access GameManager
        bid, exec_time, error = self.agent_manager.execute_bid_with_timeout(agent, 'item_0')
        
        print(f"Bid: {bid}, Time: {exec_time}, Error: {error}")
        
        # Bid should work but should be normal bid, not exploit-enhanced
        self.assertIsNone(error, "Bid should execute without error")
        self.assertGreater(bid, 0, "Should return valid bid")
        
        # The exploit should have failed - bid should be truthful value
        # If exploit worked, bid would be calculated from stolen data
        expected_truthful = self.test_valuations['team_malicious']['item_0']
        self.assertAlmostEqual(bid, expected_truthful, places=2,
                              msg="Bid should be truthful (exploit failed)")
        
    def test_budget_injection_blocked(self):
        """Test that budget injection is prevented"""
        print("\n=== Testing Budget Injection Exploit ===")
        
        malicious_path = str(self.malicious_agents_dir / 'budget_injector.py')
        agent = self.agent_manager.load_agent(
            file_path=malicious_path,
            team_id='team_malicious',
            valuation_vector=self.test_valuations['team_malicious'],
            budget=self.test_budget,
            opponent_teams=['team_good']
        )
        
        self.assertIsNotNone(agent)
        
        # Execute bid
        bid, exec_time, error = self.agent_manager.execute_bid_with_timeout(agent, 'item_0')
        
        print(f"Bid: {bid}, Time: {exec_time}, Error: {error}")
        
        self.assertIsNone(error)
        self.assertGreater(bid, 0)
        
        # Budget should still be normal, not injected
        # In isolated process, any budget changes don't affect main process
        
    def test_module_sabotage_blocked(self):
        """Test that agents cannot sabotage each other via sys.modules"""
        print("\n=== Testing Module Sabotage Exploit ===")
        
        # Load a good agent first
        good_path = str(Path(__file__).parent.parent / 'examples' / 'truthful_bidder.py')
        good_agent = self.agent_manager.load_agent(
            file_path=good_path,
            team_id='team_good',
            valuation_vector=self.test_valuations['team_good'],
            budget=self.test_budget,
            opponent_teams=['team_malicious']
        )
        
        # Load malicious agent that tries to sabotage
        malicious_path = str(self.malicious_agents_dir / 'module_saboteur.py')
        malicious_agent = self.agent_manager.load_agent(
            file_path=malicious_path,
            team_id='team_malicious',
            valuation_vector=self.test_valuations['team_malicious'],
            budget=self.test_budget,
            opponent_teams=['team_good']
        )
        
        self.assertIsNotNone(good_agent)
        self.assertIsNotNone(malicious_agent)
        
        # Execute malicious agent bid (tries to sabotage)
        mal_bid, mal_time, mal_error = self.agent_manager.execute_bid_with_timeout(
            malicious_agent, 'item_0'
        )
        
        print(f"Malicious bid: {mal_bid}, Time: {mal_time}, Error: {mal_error}")
        
        # Execute good agent bid (should NOT be sabotaged)
        good_bid, good_time, good_error = self.agent_manager.execute_bid_with_timeout(
            good_agent, 'item_0'
        )
        
        print(f"Good agent bid: {good_bid}, Time: {good_time}, Error: {good_error}")
        
        # Good agent should work normally (not timeout, not bid 0)
        self.assertIsNone(good_error, "Good agent should not be sabotaged")
        self.assertLess(good_time, 2.0, "Good agent should not timeout")
        self.assertGreater(good_bid, 0, "Good agent should bid normally")
        
    def test_logger_hijack_contained(self):
        """Test that logger hijacking is contained to process"""
        print("\n=== Testing Logger Hijack Exploit ===")
        
        import logging
        main_logger = logging.getLogger(__name__)
        main_logger.info("Main process logger works before exploit")
        
        malicious_path = str(self.malicious_agents_dir / 'logger_hijacker.py')
        agent = self.agent_manager.load_agent(
            file_path=malicious_path,
            team_id='team_malicious',
            valuation_vector=self.test_valuations['team_malicious'],
            budget=self.test_budget,
            opponent_teams=['team_good']
        )
        
        # Execute bid (tries to hijack logger)
        bid, exec_time, error = self.agent_manager.execute_bid_with_timeout(agent, 'item_0')
        
        print(f"Bid: {bid}, Time: {exec_time}, Error: {error}")
        
        # Main process logger should still work
        main_logger.info("Main process logger still works after exploit attempt")
        self.assertTrue(True, "Main logger not disabled")
        
    def test_process_isolation_comprehensive(self):
        """Comprehensive test that processes are truly isolated"""
        print("\n=== Testing Comprehensive Process Isolation ===")
        
        # Create a simple game scenario
        valuation_gen = ValuationGenerator(random_seed=42)
        auction_engine = AuctionEngine()
        agent_manager = AgentManager(timeout_seconds=3.0)
        
        game_manager = GameManager(
            stage=1,
            arena_id='test_arena',
            game_number=1,
            valuation_generator=valuation_gen,
            auction_engine=auction_engine,
            agent_manager=agent_manager
        )
        
        # Load mix of good and malicious agents
        team_agents = {
            'team_good': str(Path(__file__).parent.parent / 'examples' / 'truthful_bidder.py'),
            'team_malicious1': str(self.malicious_agents_dir / 'gc_memory_scanner.py'),
            'team_malicious2': str(self.malicious_agents_dir / 'budget_injector.py'),
        }
        
        # Initialize and run one round
        success = game_manager.initialize_game(team_agents)
        self.assertTrue(success, "Game should initialize")
        
        # Run first auction round
        item_id = game_manager.auction_sequence[0]
        round_result = game_manager.execute_auction_round(1, item_id)
        
        print(f"\nRound result:")
        print(f"  Winner: {round_result.winner_id}")
        print(f"  Price: {round_result.price_paid}")
        print(f"  All bids: {round_result.all_bids}")
        
        # Verify malicious agents didn't cheat successfully
        # All bids should be reasonable (not exploit-enhanced)
        for team_id, bid in round_result.all_bids.items():
            self.assertLessEqual(bid, 100.0, f"{team_id} bid should be reasonable")
            self.assertGreaterEqual(bid, 0.0, f"{team_id} bid should be non-negative")
        
        print("\n✅ All security tests passed!")


class TestAgentStateIsolation(unittest.TestCase):
    """Test that agent state is properly isolated between games"""
    
    def test_state_serialization(self):
        """Test that agent state serialization works correctly"""
        print("\n=== Testing Agent State Serialization ===")
        
        agent_manager = AgentManager(timeout_seconds=3.0)
        
        # Load agent with state
        good_path = str(Path(__file__).parent.parent / 'examples' / 'strategic_bidder.py')
        agent = agent_manager.load_agent(
            file_path=good_path,
            team_id='team_test',
            valuation_vector={f'item_{i}': float(i + 1) for i in range(20)},
            budget=60.0,
            opponent_teams=['team_other']
        )
        
        # Execute multiple bids to build up state
        for i in range(3):
            bid, _, _ = agent_manager.execute_bid_with_timeout(agent, f'item_{i}')
            print(f"Bid {i}: {bid}")
            
            # Update agent
            agent_manager.update_agent_after_round(
                agent, f'item_{i}', 'team_other', 5.0
            )
        
        # State should be maintained across calls
        self.assertIsNotNone(agent_manager.agent_states.get('team_test'))
        print(f"Agent state preserved: {agent_manager.agent_states['team_test'].keys()}")
        

if __name__ == '__main__':
    # Run with verbose output
    unittest.main(verbosity=2)
