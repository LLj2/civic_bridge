"""
SQLAlchemy Models for Civic Bridge
Database models for production PostgreSQL deployment
"""

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, Text, Date, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime

db = SQLAlchemy()

class Comune(db.Model):
    """Italian municipalities model"""
    __tablename__ = 'comuni'
    
    id = Column(Integer, primary_key=True)
    istat_comune = Column(String(6), unique=True, nullable=False, index=True)
    comune = Column(String(255), nullable=False, index=True)
    provincia = Column(String(10), nullable=False, index=True)
    regione = Column(String(100), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    collegi_camera = relationship("CollegioCamera", back_populates="comune")
    collegi_senato = relationship("CollegioSenato", back_populates="comune")
    
    def __repr__(self):
        return f'<Comune {self.comune} ({self.provincia})>'
    
    def to_dict(self):
        return {
            'istat_comune': self.istat_comune,
            'comune': self.comune,
            'provincia': self.provincia,
            'regione': self.regione
        }

class CollegioCamera(db.Model):
    """Camera dei Deputati electoral districts"""
    __tablename__ = 'collegi_camera'
    
    id = Column(Integer, primary_key=True)
    istat_comune = Column(String(6), ForeignKey('comuni.istat_comune'), nullable=False, index=True)
    collegio_camera_id = Column(String(50), nullable=False, index=True)
    collegio_camera_nome = Column(String(255), nullable=False)
    fonte_url = Column(Text)
    fonte_data = Column(Date)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    comune = relationship("Comune", back_populates="collegi_camera")
    deputati = relationship("Deputato", back_populates="collegio_obj")
    
    def __repr__(self):
        return f'<CollegioCamera {self.collegio_camera_id}>'

class CollegioSenato(db.Model):
    """Senato electoral districts"""
    __tablename__ = 'collegi_senato'
    
    id = Column(Integer, primary_key=True)
    istat_comune = Column(String(6), ForeignKey('comuni.istat_comune'), nullable=False, index=True)
    collegio_senato_id = Column(String(50), nullable=False, index=True)
    collegio_senato_nome = Column(String(255), nullable=False)
    fonte_url = Column(Text)
    fonte_data = Column(Date)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    comune = relationship("Comune", back_populates="collegi_senato")
    senatori = relationship("Senatore", back_populates="collegio_obj")
    
    def __repr__(self):
        return f'<CollegioSenato {self.collegio_senato_id}>'

class Deputato(db.Model):
    """Camera dei Deputati representatives"""
    __tablename__ = 'deputati'
    
    id = Column(Integer, primary_key=True)
    persona_uri = Column(Text, unique=True, nullable=False)
    cognome = Column(String(255), nullable=False, index=True)
    nome = Column(String(255), nullable=False)
    info = Column(Text)
    data_nascita = Column(Date)
    luogo_nascita = Column(String(255))
    genere = Column(String(20))
    collegio = Column(String(255), index=True)
    lista = Column(String(255))
    nome_gruppo = Column(String(255), index=True)
    numero_mandati = Column(Integer, default=1)
    email = Column(String(255))
    aggiornamento = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    collegio_obj = relationship("CollegioCamera", back_populates="deputati", 
                               foreign_keys=[collegio], 
                               primaryjoin="Deputato.collegio == CollegioCamera.collegio_camera_id")
    
    def __repr__(self):
        return f'<Deputato {self.nome} {self.cognome}>'
    
    def to_dict(self):
        return {
            'nome': self.nome,
            'cognome': self.cognome,
            'info': self.info,
            'data_nascita': self.data_nascita.isoformat() if self.data_nascita else None,
            'luogo_nascita': self.luogo_nascita,
            'genere': self.genere,
            'collegio': self.collegio,
            'lista': self.lista,
            'nome_gruppo': self.nome_gruppo,
            'numero_mandati': self.numero_mandati,
            'email': self.email
        }

class Senatore(db.Model):
    """Senato representatives"""
    __tablename__ = 'senatori'
    
    id = Column(Integer, primary_key=True)
    senatore_uri = Column(Text, unique=True, nullable=False)
    nome = Column(String(255), nullable=False)
    cognome = Column(String(255), nullable=False, index=True)
    inizio_mandato = Column(Date)
    legislatura = Column(Integer)
    tipo_mandato = Column(String(50))
    email = Column(String(255))
    telefono = Column(String(50))
    collegio = Column(String(255), index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    collegio_obj = relationship("CollegioSenato", back_populates="senatori",
                               foreign_keys=[collegio],
                               primaryjoin="Senatore.collegio == CollegioSenato.collegio_senato_id")
    
    def __repr__(self):
        return f'<Senatore {self.nome} {self.cognome}>'
    
    def to_dict(self):
        return {
            'nome': self.nome,
            'cognome': self.cognome,
            'inizio_mandato': self.inizio_mandato.isoformat() if self.inizio_mandato else None,
            'legislatura': self.legislatura,
            'tipo_mandato': self.tipo_mandato,
            'email': self.email,
            'telefono': self.telefono,
            'collegio': self.collegio
        }

class EURepresentative(db.Model):
    """EU Parliament representatives"""
    __tablename__ = 'eu_representatives'
    
    id = Column(Integer, primary_key=True)
    nome = Column(String(255), nullable=False)
    cognome = Column(String(255), nullable=False, index=True)
    email = Column(String(255))
    telefono = Column(String(50))
    constituency = Column(String(255))
    party = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<EURepresentative {self.nome} {self.cognome}>'
    
    def to_dict(self):
        return {
            'nome': self.nome,
            'cognome': self.cognome,
            'email': self.email,
            'telefono': self.telefono,
            'constituency': self.constituency,
            'party': self.party
        }

# Additional indexes for performance
Index('idx_comuni_search', Comune.comune, Comune.provincia, Comune.regione)
Index('idx_deputati_search', Deputato.cognome, Deputato.nome, Deputato.collegio)
Index('idx_senatori_search', Senatore.cognome, Senatore.nome, Senatore.collegio)