-- Civic Bridge Database Schema
-- PostgreSQL schema for production deployment

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Drop tables if they exist (for clean migrations)
DROP TABLE IF EXISTS eu_representatives CASCADE;
DROP TABLE IF EXISTS senatori CASCADE;
DROP TABLE IF EXISTS deputati CASCADE;
DROP TABLE IF EXISTS collegi_senato CASCADE;
DROP TABLE IF EXISTS collegi_camera CASCADE;
DROP TABLE IF EXISTS comuni CASCADE;

-- Comuni (Italian municipalities)
CREATE TABLE comuni (
    id SERIAL PRIMARY KEY,
    istat_comune VARCHAR(6) UNIQUE NOT NULL,
    comune VARCHAR(255) NOT NULL,
    provincia VARCHAR(10) NOT NULL,
    regione VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Camera dei Deputati electoral districts
CREATE TABLE collegi_camera (
    id SERIAL PRIMARY KEY,
    istat_comune VARCHAR(6) NOT NULL,
    collegio_camera_id VARCHAR(50) NOT NULL,
    collegio_camera_nome VARCHAR(255) NOT NULL,
    fonte_url TEXT,
    fonte_data DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (istat_comune) REFERENCES comuni(istat_comune) ON DELETE CASCADE
);

-- Senato electoral districts
CREATE TABLE collegi_senato (
    id SERIAL PRIMARY KEY,
    istat_comune VARCHAR(6) NOT NULL,
    collegio_senato_id VARCHAR(50) NOT NULL,
    collegio_senato_nome VARCHAR(255) NOT NULL,
    fonte_url TEXT,
    fonte_data DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (istat_comune) REFERENCES comuni(istat_comune) ON DELETE CASCADE
);

-- Camera dei Deputati representatives
CREATE TABLE deputati (
    id SERIAL PRIMARY KEY,
    persona_uri TEXT UNIQUE NOT NULL,
    cognome VARCHAR(255) NOT NULL,
    nome VARCHAR(255) NOT NULL,
    info TEXT,
    data_nascita DATE,
    luogo_nascita VARCHAR(255),
    genere VARCHAR(20),
    collegio VARCHAR(255),
    lista VARCHAR(255),
    nome_gruppo VARCHAR(255),
    numero_mandati INTEGER DEFAULT 1,
    email VARCHAR(255),
    aggiornamento TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Senato representatives
CREATE TABLE senatori (
    id SERIAL PRIMARY KEY,
    senatore_uri TEXT UNIQUE NOT NULL,
    nome VARCHAR(255) NOT NULL,
    cognome VARCHAR(255) NOT NULL,
    inizio_mandato DATE,
    legislatura INTEGER,
    tipo_mandato VARCHAR(50),
    email VARCHAR(255),
    telefono VARCHAR(50),
    collegio VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- EU Parliament representatives (placeholder structure)
CREATE TABLE eu_representatives (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(255) NOT NULL,
    cognome VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    telefono VARCHAR(50),
    constituency VARCHAR(255),
    party VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX idx_comuni_comune_trgm ON comuni USING gin (comune gin_trgm_ops);
CREATE INDEX idx_comuni_provincia ON comuni(provincia);
CREATE INDEX idx_comuni_regione ON comuni(regione);
CREATE INDEX idx_comuni_istat ON comuni(istat_comune);

CREATE INDEX idx_collegi_camera_istat ON collegi_camera(istat_comune);
CREATE INDEX idx_collegi_camera_id ON collegi_camera(collegio_camera_id);

CREATE INDEX idx_collegi_senato_istat ON collegi_senato(istat_comune);
CREATE INDEX idx_collegi_senato_id ON collegi_senato(collegio_senato_id);

CREATE INDEX idx_deputati_cognome ON deputati(cognome);
CREATE INDEX idx_deputati_collegio ON deputati(collegio);
CREATE INDEX idx_deputati_gruppo ON deputati(nome_gruppo);

CREATE INDEX idx_senatori_cognome ON senatori(cognome);
CREATE INDEX idx_senatori_collegio ON senatori(collegio);

-- Create a function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
CREATE TRIGGER update_comuni_updated_at BEFORE UPDATE ON comuni FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_deputati_updated_at BEFORE UPDATE ON deputati FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_senatori_updated_at BEFORE UPDATE ON senatori FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_eu_representatives_updated_at BEFORE UPDATE ON eu_representatives FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create a view for complete lookup data
CREATE VIEW complete_representatives AS
SELECT 
    c.istat_comune,
    c.comune,
    c.provincia,
    c.regione,
    cc.collegio_camera_id,
    cc.collegio_camera_nome,
    cs.collegio_senato_id,
    cs.collegio_senato_nome,
    d.nome as deputato_nome,
    d.cognome as deputato_cognome,
    d.email as deputato_email,
    d.nome_gruppo as deputato_gruppo,
    s.nome as senatore_nome,
    s.cognome as senatore_cognome,
    s.email as senatore_email
FROM comuni c
LEFT JOIN collegi_camera cc ON c.istat_comune = cc.istat_comune
LEFT JOIN collegi_senato cs ON c.istat_comune = cs.istat_comune
LEFT JOIN deputati d ON cc.collegio_camera_id = d.collegio
LEFT JOIN senatori s ON cs.collegio_senato_id = s.collegio;

-- Grant permissions (adjust for your user)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO civic_bridge_user;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO civic_bridge_user;