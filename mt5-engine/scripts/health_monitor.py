#!/usr/bin/env python3
"""Health monitoring for headless MT5 container."""
import os
import subprocess
import json
from datetime import datetime

class HealthMonitor:
    def __init__(self):
        self.container_id = os.getenv('HOSTNAME', 'unknown')
        self.user_id = os.getenv('USER_ID', 'test')
    
    def check_process(self):
        """Check if MT5 process is running."""
        try:
            result = subprocess.run(['pgrep', '-f', 'terminal.exe'], 
                                  capture_output=True)
            return result.returncode == 0
        except:
            return False
    
    def check_memory(self):
        """Check memory usage."""
        try:
            result = subprocess.run(['free', '-m'], capture_output=True, 
                                  text=True)
            lines = result.stdout.split('\n')
            mem_line = lines[1].split()
            used = int(mem_line[2])
            total = int(mem_line[1])
            return {'used_mb': used, 'total_mb': total, 'percent': 
                   (used/total)*100}
        except:
            return None
    
    def is_healthy(self):
        """Overall health check."""
        process_ok = self.check_process()
        memory = self.check_memory()
        
        if not process_ok:
            return False
        
        if memory and memory['percent'] > 90:
            return False
        
        return True

if __name__ == '__main__':
    monitor = HealthMonitor()
    health = monitor.is_healthy()
    
    print(json.dumps({
        'status': 'healthy' if health else 'unhealthy',
        'timestamp': datetime.utcnow().isoformat(),
        'memory': monitor.check_memory(),
        'process_running': monitor.check_process()
    }))
    
    exit(0 if health else 1)
