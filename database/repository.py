"""
Database Repository Layer for Civic Bridge
Handles database queries with caching and optimization
"""

from typing import List, Dict, Optional, Tuple
from sqlalchemy import and_, or_, func
from sqlalchemy.orm import joinedload
from flask import current_app
from .models import db, Comune, CollegioCamera, CollegioSenato, Deputato, Senatore, EURepresentative
import logging

logger = logging.getLogger(__name__)

class CivicBridgeRepository:
    """Repository class for all civic bridge database operations"""
    
    def __init__(self):
        self.db = db
    
    def search_comuni(self, query: str, limit: int = 100) -> List[Dict]:
        """
        Search for comuni with autocomplete functionality
        Uses PostgreSQL full-text search for better performance
        """
        try:
            if len(query) < 2:
                return []
            
            # Use ILIKE for case-insensitive search with trigram index
            search_pattern = f"%{query}%"
            
            results = db.session.query(Comune)\
                .filter(Comune.comune.ilike(search_pattern))\
                .order_by(Comune.comune)\
                .limit(limit)\
                .all()
            
            return [
                {
                    'comune': comune.comune,
                    'provincia': comune.provincia,
                    'regione': comune.regione,
                    'istat_comune': comune.istat_comune,
                    'display': f"{comune.comune} ({comune.provincia}) - {comune.regione}"
                }
                for comune in results
            ]
            
        except Exception as e:
            logger.error(f"Error searching comuni: {e}")
            return []
    
    def get_comune_by_name(self, comune_name: str, provincia: Optional[str] = None) -> Optional[Comune]:
        """Get a specific comune by name and optionally provincia"""
        try:
            query = db.session.query(Comune).filter(
                func.lower(Comune.comune) == func.lower(comune_name.strip())
            )
            
            if provincia:
                query = query.filter(
                    func.lower(Comune.provincia) == func.lower(provincia.strip())
                )
            
            return query.first()
            
        except Exception as e:
            logger.error(f"Error getting comune by name: {e}")
            return None
    
    def get_representatives_by_comune(self, comune: Comune) -> Dict:
        """
        Get all representatives for a given comune
        Returns camera, senato, and EU representatives
        """
        try:
            result = {
                'comune': comune.to_dict(),
                'camera': [],
                'senato': [],
                'eu': []
            }
            
            # Get Camera representatives
            camera_collegi = db.session.query(CollegioCamera)\
                .filter(CollegioCamera.istat_comune == comune.istat_comune)\
                .all()
            
            for collegio in camera_collegi:
                deputati = db.session.query(Deputato)\
                    .filter(Deputato.collegio == collegio.collegio_camera_id)\
                    .all()
                
                for deputato in deputati:
                    result['camera'].append({
                        **deputato.to_dict(),
                        'collegio_nome': collegio.collegio_camera_nome
                    })
            
            # Get Senato representatives
            senato_collegi = db.session.query(CollegioSenato)\
                .filter(CollegioSenato.istat_comune == comune.istat_comune)\
                .all()
            
            for collegio in senato_collegi:
                senatori = db.session.query(Senatore)\
                    .filter(Senatore.collegio == collegio.collegio_senato_id)\
                    .all()
                
                for senatore in senatori:
                    result['senato'].append({
                        **senatore.to_dict(),
                        'collegio_nome': collegio.collegio_senato_nome
                    })
            
            # Get EU representatives (by region)
            eu_reps = db.session.query(EURepresentative)\
                .filter(EURepresentative.constituency.ilike(f"%{comune.regione}%"))\
                .all()
            
            result['eu'] = [rep.to_dict() for rep in eu_reps]
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting representatives for comune {comune.comune}: {e}")
            return {
                'comune': comune.to_dict() if comune else {},
                'camera': [],
                'senato': [],
                'eu': []
            }
    
    def get_all_camera_representatives(self) -> List[Dict]:
        """Get all Camera representatives"""
        try:
            deputati = db.session.query(Deputato)\
                .options(joinedload(Deputato.collegio_obj))\
                .all()
            
            return [deputato.to_dict() for deputato in deputati]
            
        except Exception as e:
            logger.error(f"Error getting camera representatives: {e}")
            return []
    
    def get_all_senato_representatives(self) -> List[Dict]:
        """Get all Senato representatives"""
        try:
            senatori = db.session.query(Senatore)\
                .options(joinedload(Senatore.collegio_obj))\
                .all()
            
            return [senatore.to_dict() for senatore in senatori]
            
        except Exception as e:
            logger.error(f"Error getting senato representatives: {e}")
            return []
    
    def get_all_eu_representatives(self) -> List[Dict]:
        """Get all EU representatives"""
        try:
            eu_reps = db.session.query(EURepresentative).all()
            return [rep.to_dict() for rep in eu_reps]
            
        except Exception as e:
            logger.error(f"Error getting EU representatives: {e}")
            return []
    
    def get_health_stats(self) -> Dict:
        """Get database health statistics"""
        try:
            stats = {
                'comuni_count': db.session.query(func.count(Comune.id)).scalar(),
                'deputati_count': db.session.query(func.count(Deputato.id)).scalar(),
                'senatori_count': db.session.query(func.count(Senatore.id)).scalar(),
                'eu_representatives_count': db.session.query(func.count(EURepresentative.id)).scalar(),
                'last_updated': db.session.query(func.max(Comune.updated_at)).scalar(),
                'database_status': 'healthy'
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting health stats: {e}")
            return {
                'database_status': 'error',
                'error': str(e)
            }
    
    def bulk_insert_comuni(self, comuni_data: List[Dict]) -> int:
        """Bulk insert comuni data"""
        try:
            comune_objects = [
                Comune(
                    istat_comune=data['istat_comune'],
                    comune=data['comune'],
                    provincia=data['provincia'],
                    regione=data['regione']
                )
                for data in comuni_data
            ]
            
            db.session.bulk_save_objects(comune_objects)
            db.session.commit()
            
            return len(comune_objects)
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error bulk inserting comuni: {e}")
            raise
    
    def update_representative_contacts(self, representative_type: str, updates: List[Tuple[int, str]]) -> int:
        """Bulk update representative email contacts"""
        try:
            count = 0
            
            if representative_type == 'camera':
                for rep_id, email in updates:
                    db.session.query(Deputato)\
                        .filter(Deputato.id == rep_id)\
                        .update({'email': email})
                    count += 1
                        
            elif representative_type == 'senato':
                for rep_id, email in updates:
                    db.session.query(Senatore)\
                        .filter(Senatore.id == rep_id)\
                        .update({'email': email})
                    count += 1
            
            db.session.commit()
            return count
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating {representative_type} contacts: {e}")
            raise