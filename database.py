"""
Database schema setup for RL-based investment decision system.
Includes conversations, decision history, and RL state tracking.
"""
import sqlite3
import logging
from datetime import datetime
from typing import Optional, Dict, List, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Manages SQLite database for conversation history, decisions, and RL state.
    """
    
    def __init__(self, db_path: str = "kautilya.db"):
        """
        Initialize database manager.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.conn = None
        self.initialize_database()
        
    def initialize_database(self):
        """Create database tables and indexes if they don't exist."""
        logger.info(f"Initializing database at {self.db_path}")
        
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row  # Enable column access by name
        
        cursor = self.conn.cursor()
        
        # Create conversations table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                conversation_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT
            )
        """)
        
        # Create conversation_turns table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversation_turns (
                turn_id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id TEXT NOT NULL,
                turn_number INTEGER NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                user_question TEXT NOT NULL,
                symbol TEXT NOT NULL,
                sector TEXT,
                decision TEXT,
                confidence REAL,
                decision_json TEXT,
                FOREIGN KEY (conversation_id) REFERENCES conversations(conversation_id)
            )
        """)
        
        # Create decision_history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS decision_history (
                decision_id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                symbol TEXT NOT NULL,
                sector TEXT,
                decision TEXT NOT NULL,
                confidence REAL NOT NULL,
                weights_used TEXT,
                market_regime TEXT,
                agent_outputs TEXT,
                outcome_7d REAL,
                reward REAL,
                evaluated BOOLEAN DEFAULT 0,
                conversation_id TEXT,
                turn_number INTEGER
            )
        """)
        
        # Create rl_state table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS rl_state (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                regime_key TEXT NOT NULL,
                agent_name TEXT NOT NULL,
                alpha REAL NOT NULL DEFAULT 1.0,
                beta REAL NOT NULL DEFAULT 1.0,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(regime_key, agent_name)
            )
        """)
        
        # Create indexes for fast querying
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_conversations_user 
            ON conversations(user_id)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_turns_conversation 
            ON conversation_turns(conversation_id, turn_number)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_decisions_symbol 
            ON decision_history(symbol, timestamp)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_decisions_regime 
            ON decision_history(market_regime)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_rl_state_regime 
            ON rl_state(regime_key)
        """)
        
        self.conn.commit()
        logger.info("Database initialized successfully")
        
    def create_conversation(
        self, 
        conversation_id: str, 
        user_id: str, 
        metadata: Optional[str] = None
    ) -> bool:
        """Create a new conversation."""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                INSERT INTO conversations (conversation_id, user_id, metadata)
                VALUES (?, ?, ?)
                """,
                (conversation_id, user_id, metadata)
            )
            self.conn.commit()
            logger.info(f"Created conversation {conversation_id} for user {user_id}")
            return True
        except sqlite3.IntegrityError:
            logger.warning(f"Conversation {conversation_id} already exists")
            return False
            
    def add_conversation_turn(
        self,
        conversation_id: str,
        turn_number: int,
        user_question: str,
        symbol: str,
        sector: Optional[str] = None,
        decision: Optional[str] = None,
        confidence: Optional[float] = None,
        decision_json: Optional[str] = None
    ) -> int:
        """Add a turn to a conversation."""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO conversation_turns 
            (conversation_id, turn_number, user_question, symbol, sector, decision, confidence, decision_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (conversation_id, turn_number, user_question, symbol, sector, decision, confidence, decision_json)
        )
        self.conn.commit()
        return cursor.lastrowid
        
    def get_conversation_history(
        self, 
        conversation_id: str, 
        last_n: int = 3
    ) -> List[Dict[str, Any]]:
        """Get last N turns of a conversation."""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT * FROM conversation_turns
            WHERE conversation_id = ?
            ORDER BY turn_number DESC
            LIMIT ?
            """,
            (conversation_id, last_n)
        )
        
        rows = cursor.fetchall()
        return [dict(row) for row in reversed(rows)]
        
    def record_decision(
        self,
        symbol: str,
        decision: str,
        confidence: float,
        sector: Optional[str] = None,
        weights_used: Optional[str] = None,
        market_regime: Optional[str] = None,
        agent_outputs: Optional[str] = None,
        conversation_id: Optional[str] = None,
        turn_number: Optional[int] = None
    ) -> int:
        """Record a decision in the decision history."""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO decision_history 
            (symbol, sector, decision, confidence, weights_used, market_regime, 
             agent_outputs, conversation_id, turn_number)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (symbol, sector, decision, confidence, weights_used, market_regime,
             agent_outputs, conversation_id, turn_number)
        )
        self.conn.commit()
        decision_id = cursor.lastrowid
        logger.info(f"Recorded decision {decision_id} for {symbol}: {decision}")
        return decision_id
        
    def update_decision_outcome(
        self,
        decision_id: int,
        outcome_7d: float,
        reward: float
    ):
        """Update a decision with its outcome and reward."""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            UPDATE decision_history
            SET outcome_7d = ?, reward = ?, evaluated = 1
            WHERE decision_id = ?
            """,
            (outcome_7d, reward, decision_id)
        )
        self.conn.commit()
        logger.info(f"Updated decision {decision_id} with outcome {outcome_7d:.2f}% and reward {reward:.4f}")
        
    def get_unevaluated_decisions(self) -> List[Dict[str, Any]]:
        """Get all decisions that haven't been evaluated yet."""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT * FROM decision_history
            WHERE evaluated = 0
            ORDER BY timestamp ASC
            """
        )
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
        
    def get_decisions_by_regime(self, regime_key: str) -> List[Dict[str, Any]]:
        """Get all decisions for a specific market regime."""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT * FROM decision_history
            WHERE market_regime = ?
            ORDER BY timestamp DESC
            """,
            (regime_key,)
        )
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
        
    def get_rl_state(self, regime_key: str, agent_name: str) -> Optional[Dict[str, float]]:
        """Get RL state (alpha, beta) for a specific regime-agent pair."""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT alpha, beta FROM rl_state
            WHERE regime_key = ? AND agent_name = ?
            """,
            (regime_key, agent_name)
        )
        row = cursor.fetchone()
        if row:
            return {"alpha": row["alpha"], "beta": row["beta"]}
        return None
        
    def update_rl_state(
        self,
        regime_key: str,
        agent_name: str,
        alpha: float,
        beta: float
    ):
        """Update or insert RL state for a regime-agent pair."""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO rl_state (regime_key, agent_name, alpha, beta, last_updated)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(regime_key, agent_name) 
            DO UPDATE SET 
                alpha = ?,
                beta = ?,
                last_updated = CURRENT_TIMESTAMP
            """,
            (regime_key, agent_name, alpha, beta, alpha, beta)
        )
        self.conn.commit()
        logger.debug(f"Updated RL state for {regime_key}/{agent_name}: α={alpha:.4f}, β={beta:.4f}")
        
    def get_all_rl_states(self, regime_key: str) -> Dict[str, Dict[str, float]]:
        """Get all RL states for a specific regime."""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT agent_name, alpha, beta FROM rl_state
            WHERE regime_key = ?
            """,
            (regime_key,)
        )
        rows = cursor.fetchall()
        return {
            row["agent_name"]: {"alpha": row["alpha"], "beta": row["beta"]}
            for row in rows
        }
        
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")
            
    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


if __name__ == "__main__":
    # Test database setup
    logging.basicConfig(level=logging.INFO)
    
    db = DatabaseManager("test_kautilya.db")
    
    # Test conversation creation
    db.create_conversation("conv_001", "user_123", metadata='{"test": true}')
    
    # Test conversation turn
    turn_id = db.add_conversation_turn(
        "conv_001", 1, "Should I buy TCS?", "TCS", "IT",
        "BUY", 0.85, '{"decision": "BUY"}'
    )
    print(f"Created turn: {turn_id}")
    
    # Test decision recording
    decision_id = db.record_decision(
        "TCS", "BUY", 0.85, "IT",
        weights_used='{"macro": 0.3, "company": 0.7}',
        market_regime="high_inflation_rising_rates",
        conversation_id="conv_001",
        turn_number=1
    )
    print(f"Created decision: {decision_id}")
    
    # Test RL state
    db.update_rl_state("high_inflation_rising_rates", "inflation_agent", 2.5, 1.2)
    state = db.get_rl_state("high_inflation_rising_rates", "inflation_agent")
    print(f"RL state: {state}")
    
    db.close()
    print("Database tests completed")
