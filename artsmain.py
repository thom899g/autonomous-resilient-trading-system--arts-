"""
Autonomous Resilient Trading System (ARTS) - Main Orchestrator
Coordinates real-time monitoring, anomaly detection, and strategy adaptation.
"""
import asyncio
import signal
import sys
from datetime import datetime
from typing import Dict, Any, Optional
import logging
from dataclasses import asdict

from arts.data_monitor import MarketDataMonitor
from arts.anomaly_detector import StrategyAnomalyDetector
from arts.strategy_evolver import StrategyEvolver
from arts.risk_manager import AdaptiveRiskManager
from arts.firebase_client import FirebaseClient
from arts.config import ARTSConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('arts_system.log')
    ]
)
logger = logging.getLogger(__name__)


class AutonomousResilientTradingSystem:
    """
    Main ARTS controller coordinating all subsystems.
    
    Architectural Rationale:
    - Uses dependency injection for testability
    - Implements graceful shutdown handling
    - Maintains loose coupling between components
    - Ensures all state is persisted to Firebase
    """
    
    def __init__(self, config: ARTSConfig):
        self.config = config
        self.running = False
        self.components = {}
        self.firebase_client = None
        
    async def initialize(self) -> bool:
        """
        Initialize all system components with proper error handling.
        
        Edge Cases Handled:
        - Firebase connection failures
        - Component initialization failures
        - Configuration validation
        """
        try:
            logger.info("Initializing ARTS System...")
            
            # Initialize Firebase client first (critical dependency)
            self.firebase_client = FirebaseClient()
            if not await self.firebase_client.test_connection():
                logger.error("Failed to connect to Firebase. System cannot start.")
                return False
            
            # Initialize components with dependency injection
            self.components = {
                'data_monitor': MarketDataMonitor(
                    config=self.config.data_config,
                    firebase_client=self.firebase_client
                ),
                'anomaly_detector': StrategyAnomalyDetector(
                    config=self.config.anomaly_config,
                    firebase_client=self.firebase_client
                ),
                'strategy_evolver': StrategyEvolver(
                    config=self.config.evolver_config,
                    firebase_client=self.firebase_client
                ),
                'risk_manager': AdaptiveRiskManager(
                    config=self.config.risk_config,
                    firebase_client=self.firebase_client
                )
            }
            
            # Initialize each component
            for name, component in self.components.items():
                try:
                    await component.initialize()
                    logger.info(f"Component {name} initialized successfully")
                except Exception as e:
                    logger.error(f"Failed to initialize {name}: {