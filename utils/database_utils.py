"""
Database utilities for storing and retrieving contract analysis data
"""
import json
import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = "data/analysis_history.db"

def init_database():
    """Initialize SQLite database for storing analysis results"""
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS contracts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT UNIQUE NOT NULL,
            upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            file_path TEXT NOT NULL,
            analysis_json TEXT
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS compliance_issues (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            contract_id INTEGER,
            issue_title TEXT,
            risk_level TEXT,
            reason TEXT,
            FOREIGN KEY(contract_id) REFERENCES contracts(id)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS key_clauses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            contract_id INTEGER,
            clause_name TEXT,
            clause_content TEXT,
            FOREIGN KEY(contract_id) REFERENCES contracts(id)
        )
    """)
    
    conn.commit()
    conn.close()

def save_analysis(filename, file_path, analysis_data):
    """Save contract analysis to database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    analysis_json = json.dumps(analysis_data)
    
    cursor.execute("""
        INSERT OR REPLACE INTO contracts (filename, file_path, analysis_json)
        VALUES (?, ?, ?)
    """, (filename, file_path, analysis_json))
    
    contract_id = cursor.lastrowid
    
    # Save compliance issues
    for issue in analysis_data.get('issues', []):
        cursor.execute("""
            INSERT INTO compliance_issues (contract_id, issue_title, risk_level, reason)
            VALUES (?, ?, ?, ?)
        """, (contract_id, issue.get('title'), issue.get('risk_level'), issue.get('reason')))
    
    # Save key clauses
    for clause in analysis_data.get('clauses', []):
        cursor.execute("""
            INSERT INTO key_clauses (contract_id, clause_name, clause_content)
            VALUES (?, ?, ?)
        """, (contract_id, clause, ""))
    
    conn.commit()
    conn.close()
    return contract_id

def get_all_contracts():
    """Get list of all analyzed contracts"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM contracts ORDER BY upload_date DESC")
    contracts = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    return contracts

def get_contract_analysis(contract_id):
    """Get analysis for a specific contract"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM contracts WHERE id = ?", (contract_id,))
    contract = dict(cursor.fetchone())
    
    cursor.execute("SELECT * FROM compliance_issues WHERE contract_id = ?", (contract_id,))
    issues = [dict(row) for row in cursor.fetchall()]
    
    cursor.execute("SELECT * FROM key_clauses WHERE contract_id = ?", (contract_id,))
    clauses = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    
    return {
        'contract': contract,
        'issues': issues,
        'clauses': clauses
    }

# Initialize database on import
init_database()
