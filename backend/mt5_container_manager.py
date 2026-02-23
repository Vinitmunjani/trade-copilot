"""Manage MT5 Docker containers - launch, monitor, retrieve data."""
import docker
import json
import time
import requests
from typing import Dict, Any, Optional

class MT5ContainerManager:
    """Launch and manage MT5 terminals in Docker."""
    
    def __init__(self):
        self.client = docker.from_env()
        self.containers = {}
    
    def launch_terminal(self, user_id: str, broker: str, login: str, password: str, server: str) -> Dict[str, Any]:
        """
        Launch MT5 terminal in Docker container.
        
        Returns:
            {
                "status": "success|failed",
                "container_id": "abc123...",
                "port": 5000,
                "api_url": "http://container:5000",
                "error": "message" (if failed)
            }
        """
        try:
            container_name = f"mt5-{user_id}-{broker.lower()}"
            
            # Check if container already running
            try:
                existing = self.client.containers.get(container_name)
                if existing.status == "running":
                    return {
                        "status": "success",
                        "message": "Container already running",
                        "container_id": existing.id,
                        "port": 5000
                    }
            except docker.errors.NotFound:
                pass
            
            # Find available port
            port = self._find_available_port(5001, 5100)
            
            # Launch container
            container = self.client.containers.run(
                "mt5-engine:latest",
                name=container_name,
                environment={
                    "BROKER": broker,
                    "LOGIN": login,
                    "PASSWORD": password,
                    "SERVER": server,
                    "USER_ID": user_id,
                },
                ports={"5000/tcp": port},
                detach=True,
                remove=False
            )
            
            # Store container reference
            self.containers[user_id] = {
                "container_id": container.id,
                "container_name": container_name,
                "port": port,
                "broker": broker,
                "login": login,
                "server": server
            }
            
            # Wait for API to be ready
            time.sleep(3)
            
            # Verify container is running
            container.reload()
            if container.status != "running":
                return {
                    "status": "failed",
                    "error": f"Container failed to start"
                }
            
            # Test API endpoint
            try:
                resp = requests.get(f"http://localhost:{port}/health", timeout=5)
                if resp.status_code == 200:
                    return {
                        "status": "success",
                        "container_id": container.id,
                        "port": port,
                        "message": "Container launched and API ready"
                    }
            except:
                pass
            
            return {
                "status": "success",
                "container_id": container.id,
                "port": port,
                "message": "Container launched (API initializing)"
            }
            
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e)
            }
    
    def get_account_info(self, user_id: str) -> Dict[str, Any]:
        """Get account info from running terminal."""
        if user_id not in self.containers:
            return {"status": "error", "error": "Container not found"}
        
        port = self.containers[user_id]["port"]
        
        try:
            resp = requests.get(f"http://localhost:{port}/account", timeout=5)
            if resp.status_code == 200:
                return resp.json()
        except:
            pass
        
        return {"status": "error", "error": "Could not retrieve account info"}
    
    def get_trades(self, user_id: str) -> list:
        """Get open trades from running terminal."""
        if user_id not in self.containers:
            return []
        
        port = self.containers[user_id]["port"]
        
        try:
            resp = requests.get(f"http://localhost:{port}/trades", timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                return data.get("trades", [])
        except:
            pass
        
        return []
    
    def stop_terminal(self, user_id: str) -> Dict[str, Any]:
        """Stop MT5 terminal container."""
        if user_id not in self.containers:
            return {"status": "error", "error": "Container not found"}
        
        try:
            container = self.client.containers.get(self.containers[user_id]["container_id"])
            container.stop()
            del self.containers[user_id]
            return {"status": "success", "message": "Container stopped"}
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def _find_available_port(self, start: int, end: int) -> int:
        """Find available port in range."""
        import socket
        for port in range(start, end):
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.bind(("", port))
                s.close()
                return port
            except:
                continue
        raise Exception(f"No available ports between {start} and {end}")

# Global manager instance
mt5_manager = MT5ContainerManager()
