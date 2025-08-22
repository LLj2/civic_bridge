#!/usr/bin/env python3
"""
CSV to PostgreSQL Migration Script for Civic Bridge
Migrates all CSV data to PostgreSQL database
"""

import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
import os
import sys
from pathlib import Path
import logging
from datetime import datetime
import argparse

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CivicBridgeMigrator:
    def __init__(self, db_config, data_dir="data"):
        self.db_config = db_config
        self.data_dir = Path(data_dir)
        self.conn = None
        
    def connect_db(self):
        """Connect to PostgreSQL database"""
        try:
            self.conn = psycopg2.connect(**self.db_config)
            self.conn.autocommit = False
            logger.info("Database connection established")
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            raise
    
    def close_db(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")
    
    def execute_sql_file(self, sql_file):
        """Execute SQL file to create schema"""
        try:
            with open(sql_file, 'r', encoding='utf-8') as f:
                sql_content = f.read()
            
            cursor = self.conn.cursor()
            cursor.execute(sql_content)
            self.conn.commit()
            logger.info(f"Successfully executed {sql_file}")
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Error executing {sql_file}: {e}")
            raise
    
    def migrate_comuni(self):
        """Migrate comuni.csv to comuni table"""
        logger.info("Migrating comuni...")
        
        csv_file = self.data_dir / "comuni.csv"
        if not csv_file.exists():
            logger.warning(f"File {csv_file} not found, skipping comuni migration")
            return
        
        df = pd.read_csv(csv_file)
        
        # Clean data
        df = df.dropna(subset=['istat_comune', 'comune'])
        df['comune'] = df['comune'].str.strip()
        df['provincia'] = df['provincia'].str.strip()
        df['regione'] = df['regione'].str.strip()
        
        # Prepare data for insertion
        data = [(
            row['istat_comune'],
            row['comune'],
            row['provincia'],
            row['regione']
        ) for _, row in df.iterrows()]
        
        # Insert data
        cursor = self.conn.cursor()
        execute_values(
            cursor,
            """INSERT INTO comuni (istat_comune, comune, provincia, regione) 
               VALUES %s ON CONFLICT (istat_comune) DO NOTHING""",
            data
        )
        self.conn.commit()
        logger.info(f"Migrated {len(data)} comuni records")
    
    def migrate_collegi_camera(self):
        """Migrate collegi_camera.csv to collegi_camera table"""
        logger.info("Migrating collegi camera...")
        
        csv_file = self.data_dir / "collegi_camera.csv"
        if not csv_file.exists():
            logger.warning(f"File {csv_file} not found, skipping collegi camera migration")
            return
        
        df = pd.read_csv(csv_file)
        df = df.dropna(subset=['istat_comune', 'collegio_camera_id'])
        
        # Parse date if present
        if 'fonte_data' in df.columns:
            df['fonte_data'] = pd.to_datetime(df['fonte_data'], errors='coerce')
        
        data = [(
            row['istat_comune'],
            row['collegio_camera_id'],
            row.get('collegio_camera_nome', ''),
            row.get('fonte_url', ''),
            row.get('fonte_data', None)
        ) for _, row in df.iterrows()]
        
        cursor = self.conn.cursor()
        execute_values(
            cursor,
            """INSERT INTO collegi_camera (istat_comune, collegio_camera_id, collegio_camera_nome, fonte_url, fonte_data) 
               VALUES %s ON CONFLICT DO NOTHING""",
            data
        )
        self.conn.commit()
        logger.info(f"Migrated {len(data)} collegi camera records")
    
    def migrate_collegi_senato(self):
        """Migrate collegi_senato.csv to collegi_senato table"""
        logger.info("Migrating collegi senato...")
        
        csv_file = self.data_dir / "collegi_senato.csv"
        if not csv_file.exists():
            logger.warning(f"File {csv_file} not found, skipping collegi senato migration")
            return
        
        df = pd.read_csv(csv_file)
        df = df.dropna(subset=['istat_comune', 'collegio_senato_id'])
        
        if 'fonte_data' in df.columns:
            df['fonte_data'] = pd.to_datetime(df['fonte_data'], errors='coerce')
        
        data = [(
            row['istat_comune'],
            row['collegio_senato_id'],
            row.get('collegio_senato_nome', ''),
            row.get('fonte_url', ''),
            row.get('fonte_data', None)
        ) for _, row in df.iterrows()]
        
        cursor = self.conn.cursor()
        execute_values(
            cursor,
            """INSERT INTO collegi_senato (istat_comune, collegio_senato_id, collegio_senato_nome, fonte_url, fonte_data) 
               VALUES %s ON CONFLICT DO NOTHING""",
            data
        )
        self.conn.commit()
        logger.info(f"Migrated {len(data)} collegi senato records")
    
    def migrate_deputati(self):
        """Migrate deputati_XiX.csv to deputati table"""
        logger.info("Migrating deputati...")
        
        csv_file = self.data_dir / "deputati_XiX.csv"
        if not csv_file.exists():
            logger.warning(f"File {csv_file} not found, skipping deputati migration")
            return
        
        df = pd.read_csv(csv_file)
        df = df.dropna(subset=['persona', 'cognome', 'nome'])
        
        # Parse dates
        if 'dataNascita' in df.columns:
            df['dataNascita'] = pd.to_datetime(df['dataNascita'], format='%Y%m%d', errors='coerce')
        if 'aggiornamento' in df.columns:
            df['aggiornamento'] = pd.to_datetime(df['aggiornamento'], errors='coerce')
        
        data = [(
            row['persona'],
            row['cognome'],
            row['nome'],
            row.get('info', ''),
            row.get('dataNascita', None),
            row.get('luogoNascita', ''),
            row.get('genere', ''),
            row.get('collegio', ''),
            row.get('lista', ''),
            row.get('nomeGruppo', ''),
            int(row.get('numeroMandati', 1)) if pd.notna(row.get('numeroMandati')) else 1,
            None,  # email - to be populated later
            row.get('aggiornamento', None)
        ) for _, row in df.iterrows()]
        
        cursor = self.conn.cursor()
        execute_values(
            cursor,
            """INSERT INTO deputati (persona_uri, cognome, nome, info, data_nascita, luogo_nascita, 
               genere, collegio, lista, nome_gruppo, numero_mandati, email, aggiornamento) 
               VALUES %s ON CONFLICT (persona_uri) DO NOTHING""",
            data
        )
        self.conn.commit()
        logger.info(f"Migrated {len(data)} deputati records")
    
    def migrate_senatori(self):
        """Migrate senatori.csv to senatori table"""
        logger.info("Migrating senatori...")
        
        csv_file = self.data_dir / "senatori.csv"
        if not csv_file.exists():
            # Try alternative filename
            csv_file = self.data_dir / "rappresentanti_senato.csv"
            if not csv_file.exists():
                logger.warning("No senatori CSV file found, skipping senatori migration")
                return
        
        df = pd.read_csv(csv_file)
        df = df.dropna(subset=['senatore', 'nome', 'cognome'])
        
        # Parse dates
        if 'inizioMandato' in df.columns:
            df['inizioMandato'] = pd.to_datetime(df['inizioMandato'], errors='coerce')
        
        data = [(
            row['senatore'],
            row['nome'],
            row['cognome'],
            row.get('inizioMandato', None),
            int(row.get('legislatura', 19)) if pd.notna(row.get('legislatura')) else 19,
            row.get('tipoMandato', 'elettivo'),
            None,  # email - to be populated later
            None,  # telefono - to be populated later
            row.get('collegio', '')
        ) for _, row in df.iterrows()]
        
        cursor = self.conn.cursor()
        execute_values(
            cursor,
            """INSERT INTO senatori (senatore_uri, nome, cognome, inizio_mandato, legislatura, 
               tipo_mandato, email, telefono, collegio) 
               VALUES %s ON CONFLICT (senatore_uri) DO NOTHING""",
            data
        )
        self.conn.commit()
        logger.info(f"Migrated {len(data)} senatori records")
    
    def run_migration(self, schema_file=None):
        """Run complete migration"""
        logger.info("Starting CSV to PostgreSQL migration...")
        
        try:
            self.connect_db()
            
            # Create schema if provided
            if schema_file and Path(schema_file).exists():
                logger.info("Creating database schema...")
                self.execute_sql_file(schema_file)
            
            # Migrate data in order (respecting foreign keys)
            self.migrate_comuni()
            self.migrate_collegi_camera()
            self.migrate_collegi_senato()
            self.migrate_deputati()
            self.migrate_senatori()
            
            logger.info("Migration completed successfully!")
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            if self.conn:
                self.conn.rollback()
            raise
        finally:
            self.close_db()

def main():
    parser = argparse.ArgumentParser(description='Migrate Civic Bridge CSV data to PostgreSQL')
    parser.add_argument('--host', default='localhost', help='Database host')
    parser.add_argument('--port', default='5432', help='Database port')
    parser.add_argument('--database', default='civic_bridge', help='Database name')
    parser.add_argument('--user', default='civic_bridge_user', help='Database user')
    parser.add_argument('--password', help='Database password (or set PGPASSWORD env var)')
    parser.add_argument('--data-dir', default='data', help='CSV data directory')
    parser.add_argument('--schema-file', default='database/schema.sql', help='SQL schema file')
    parser.add_argument('--create-schema', action='store_true', help='Create schema before migration')
    
    args = parser.parse_args()
    
    # Database configuration
    db_config = {
        'host': args.host,
        'port': args.port,
        'database': args.database,
        'user': args.user,
        'password': args.password or os.environ.get('PGPASSWORD')
    }
    
    if not db_config['password']:
        logger.error("Password required (use --password or set PGPASSWORD environment variable)")
        sys.exit(1)
    
    # Run migration
    migrator = CivicBridgeMigrator(db_config, args.data_dir)
    
    schema_file = args.schema_file if args.create_schema else None
    migrator.run_migration(schema_file)

if __name__ == "__main__":
    main()