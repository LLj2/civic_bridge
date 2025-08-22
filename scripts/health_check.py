#!/usr/bin/env python3
"""
Civic Bridge Health Check Script
Comprehensive health monitoring for production deployment
"""

import requests
import psycopg2
import redis
import json
import sys
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class HealthChecker:
    """Health checking utility for Civic Bridge"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.results = {
            'timestamp': datetime.utcnow().isoformat(),
            'overall_status': 'unknown',
            'checks': {}
        }
    
    def check_web_application(self) -> bool:
        """Check if the web application is responding"""
        try:
            url = self.config.get('app_url', 'http://localhost:5000')
            response = requests.get(f"{url}/api/health", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                self.results['checks']['web_app'] = {
                    'status': 'healthy',
                    'response_time': response.elapsed.total_seconds(),
                    'version': data.get('version', 'unknown'),
                    'service': data.get('service', 'unknown')
                }
                return True
            else:
                self.results['checks']['web_app'] = {
                    'status': 'unhealthy',
                    'error': f"HTTP {response.status_code}",
                    'response_time': response.elapsed.total_seconds()
                }
                return False
                
        except Exception as e:
            self.results['checks']['web_app'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
            return False
    
    def check_database(self) -> bool:
        """Check PostgreSQL database connectivity and basic queries"""
        try:
            db_url = self.config.get('database_url')
            if not db_url:
                raise ValueError("Database URL not configured")
            
            start_time = time.time()
            conn = psycopg2.connect(db_url)
            cursor = conn.cursor()
            
            # Test basic connectivity
            cursor.execute("SELECT 1")
            cursor.fetchone()
            
            # Test main tables exist
            cursor.execute("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name IN ('comuni', 'deputati', 'senatori')
            """)
            tables = [row[0] for row in cursor.fetchall()]
            
            # Get record counts
            counts = {}
            for table in ['comuni', 'deputati', 'senatori']:
                if table in tables:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    counts[table] = cursor.fetchone()[0]
            
            conn.close()
            
            response_time = time.time() - start_time
            
            self.results['checks']['database'] = {
                'status': 'healthy',
                'response_time': response_time,
                'tables': tables,
                'record_counts': counts
            }
            return True
            
        except Exception as e:
            self.results['checks']['database'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
            return False
    
    def check_redis(self) -> bool:
        """Check Redis connectivity and basic operations"""
        try:
            redis_url = self.config.get('redis_url', 'redis://localhost:6379/0')
            
            start_time = time.time()
            r = redis.from_url(redis_url)
            
            # Test basic connectivity
            r.ping()
            
            # Test set/get operation
            test_key = f"health_check_{int(time.time())}"
            r.set(test_key, "test_value", ex=60)
            value = r.get(test_key)
            r.delete(test_key)
            
            if value != b"test_value":
                raise ValueError("Redis set/get test failed")
            
            # Get Redis info
            info = r.info()
            
            response_time = time.time() - start_time
            
            self.results['checks']['redis'] = {
                'status': 'healthy',
                'response_time': response_time,
                'version': info.get('redis_version'),
                'memory_usage': info.get('used_memory_human'),
                'connected_clients': info.get('connected_clients')
            }
            return True
            
        except Exception as e:
            self.results['checks']['redis'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
            return False
    
    def check_api_endpoints(self) -> bool:
        """Check critical API endpoints"""
        try:
            base_url = self.config.get('app_url', 'http://localhost:5000')
            endpoints = [
                ('/api/autocomplete?q=Milano', 'autocomplete'),
                ('/api/lookup?q=Milano', 'lookup')
            ]
            
            all_healthy = True
            endpoint_results = {}
            
            for endpoint, name in endpoints:
                try:
                    start_time = time.time()
                    response = requests.get(f"{base_url}{endpoint}", timeout=10)
                    response_time = time.time() - start_time
                    
                    if response.status_code == 200:
                        data = response.json()
                        endpoint_results[name] = {
                            'status': 'healthy',
                            'response_time': response_time,
                            'success': data.get('success', False)
                        }
                    else:
                        endpoint_results[name] = {
                            'status': 'unhealthy',
                            'error': f"HTTP {response.status_code}",
                            'response_time': response_time
                        }
                        all_healthy = False
                        
                except Exception as e:
                    endpoint_results[name] = {
                        'status': 'unhealthy',
                        'error': str(e)
                    }
                    all_healthy = False
            
            self.results['checks']['api_endpoints'] = {
                'status': 'healthy' if all_healthy else 'unhealthy',
                'endpoints': endpoint_results
            }
            
            return all_healthy
            
        except Exception as e:
            self.results['checks']['api_endpoints'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
            return False
    
    def check_disk_space(self) -> bool:
        """Check available disk space"""
        try:
            import shutil
            
            paths_to_check = [
                '/opt/civic_bridge',
                '/var/lib/docker',
                '/tmp'
            ]
            
            disk_info = {}
            all_healthy = True
            
            for path in paths_to_check:
                if os.path.exists(path):
                    total, used, free = shutil.disk_usage(path)
                    free_percent = (free / total) * 100
                    
                    disk_info[path] = {
                        'total_gb': round(total / (1024**3), 2),
                        'free_gb': round(free / (1024**3), 2),
                        'free_percent': round(free_percent, 1),
                        'status': 'healthy' if free_percent > 10 else 'warning' if free_percent > 5 else 'critical'
                    }
                    
                    if free_percent <= 5:
                        all_healthy = False
            
            self.results['checks']['disk_space'] = {
                'status': 'healthy' if all_healthy else 'unhealthy',
                'paths': disk_info
            }
            
            return all_healthy
            
        except Exception as e:
            self.results['checks']['disk_space'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
            return False
    
    def check_memory_usage(self) -> bool:
        """Check system memory usage"""
        try:
            with open('/proc/meminfo', 'r') as f:
                meminfo = f.read()
            
            lines = meminfo.split('\n')
            mem_total = None
            mem_available = None
            
            for line in lines:
                if line.startswith('MemTotal:'):
                    mem_total = int(line.split()[1]) * 1024  # Convert from kB to bytes
                elif line.startswith('MemAvailable:'):
                    mem_available = int(line.split()[1]) * 1024  # Convert from kB to bytes
            
            if mem_total and mem_available:
                used_percent = ((mem_total - mem_available) / mem_total) * 100
                
                status = 'healthy'
                if used_percent > 90:
                    status = 'critical'
                elif used_percent > 80:
                    status = 'warning'
                
                self.results['checks']['memory'] = {
                    'status': status,
                    'total_gb': round(mem_total / (1024**3), 2),
                    'available_gb': round(mem_available / (1024**3), 2),
                    'used_percent': round(used_percent, 1)
                }
                
                return status == 'healthy'
            else:
                raise ValueError("Could not parse memory information")
                
        except Exception as e:
            self.results['checks']['memory'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
            return False
    
    def run_all_checks(self) -> Dict:
        """Run all health checks and return results"""
        logger.info("Starting health checks...")
        
        checks = [
            ('web_application', self.check_web_application),
            ('database', self.check_database),
            ('redis', self.check_redis),
            ('api_endpoints', self.check_api_endpoints),
            ('disk_space', self.check_disk_space),
            ('memory_usage', self.check_memory_usage)
        ]
        
        healthy_checks = 0
        total_checks = len(checks)
        
        for check_name, check_func in checks:
            logger.info(f"Running {check_name} check...")
            try:
                if check_func():
                    healthy_checks += 1
                    logger.info(f"✅ {check_name} check passed")
                else:
                    logger.warning(f"❌ {check_name} check failed")
            except Exception as e:
                logger.error(f"❌ {check_name} check error: {e}")
        
        # Determine overall status
        if healthy_checks == total_checks:
            self.results['overall_status'] = 'healthy'
        elif healthy_checks >= total_checks * 0.7:  # 70% threshold
            self.results['overall_status'] = 'degraded'
        else:
            self.results['overall_status'] = 'unhealthy'
        
        self.results['summary'] = {
            'healthy_checks': healthy_checks,
            'total_checks': total_checks,
            'health_percentage': round((healthy_checks / total_checks) * 100, 1)
        }
        
        return self.results

def main():
    """Main health check execution"""
    
    # Configuration
    config = {
        'app_url': os.environ.get('APP_URL', 'http://localhost:5000'),
        'database_url': os.environ.get('DATABASE_URL'),
        'redis_url': os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    }
    
    # Create health checker
    checker = HealthChecker(config)
    
    # Run all checks
    results = checker.run_all_checks()
    
    # Output results
    if '--json' in sys.argv:
        print(json.dumps(results, indent=2))
    else:
        status_emoji = {
            'healthy': '✅',
            'degraded': '⚠️',
            'unhealthy': '❌'
        }
        
        print(f"\n{status_emoji.get(results['overall_status'], '❓')} Overall Status: {results['overall_status'].upper()}")
        print(f"Health Score: {results['summary']['health_percentage']}% ({results['summary']['healthy_checks']}/{results['summary']['total_checks']})")
        print(f"Timestamp: {results['timestamp']}")
        
        print("\n📊 Detailed Results:")
        for check_name, check_result in results['checks'].items():
            status = check_result['status']
            emoji = '✅' if status == 'healthy' else '⚠️' if status == 'warning' else '❌'
            print(f"  {emoji} {check_name}: {status}")
            
            if 'error' in check_result:
                print(f"    Error: {check_result['error']}")
            elif 'response_time' in check_result:
                print(f"    Response time: {check_result['response_time']:.3f}s")
    
    # Exit with appropriate code
    if results['overall_status'] == 'healthy':
        sys.exit(0)
    elif results['overall_status'] == 'degraded':
        sys.exit(1)
    else:
        sys.exit(2)

if __name__ == "__main__":
    main()