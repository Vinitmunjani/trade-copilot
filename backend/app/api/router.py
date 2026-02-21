"""Main API router aggregating all route modules."""

from fastapi import APIRouter

from app.api.auth import router as auth_router
from app.api.trades import router as trades_router
from app.api.stats import router as stats_router
from app.api.rules import router as rules_router
from app.api.analysis import router as analysis_router
from app.api.account import router as account_router
from app.api.ws import router as ws_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth_router)
api_router.include_router(trades_router)
api_router.include_router(stats_router)
api_router.include_router(rules_router)
api_router.include_router(analysis_router)
api_router.include_router(account_router)
api_router.include_router(ws_router)


# MT5 Build Status Endpoint
import json
import subprocess
import os
from fastapi import APIRouter

@router.get("/mt5/status", tags=["MT5"])
async def get_mt5_status():
    """Get MT5 Docker build and deployment status."""
    try:
        # Check Docker containers
        result = subprocess.run(
            ["docker", "ps", "-a", "--filter", "name=mt5", "--format", "{{json .}}"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        containers = []
        if result.stdout:
            for line in result.stdout.strip().split('\n'):
                if line:
                    try:
                        containers.append(json.loads(line))
                    except:
                        pass
        
        # Check build log
        build_log_path = "/tmp/docker_build.log"
        build_status = "not_started"
        build_progress = ""
        
        if os.path.exists(build_log_path):
            with open(build_log_path, 'r') as f:
                log_content = f.read()
                if "successfully built" in log_content.lower():
                    build_status = "completed"
                elif "error" in log_content.lower():
                    build_status = "failed"
                elif "step" in log_content.lower():
                    build_status = "in_progress"
                build_progress = log_content[-500:] if log_content else ""
        
        # Check if build process running
        ps_result = subprocess.run(
            ["pgrep", "-f", "docker build"],
            capture_output=True
        )
        is_building = ps_result.returncode == 0
        
        return {
            "build_status": build_status,
            "is_building": is_building,
            "containers": [{"name": c.get("Names"), "status": c.get("Status")} for c in containers],
            "container_count": len(containers),
            "build_progress_tail": build_progress
        }
    except Exception as e:
        return {
            "error": str(e),
            "build_status": "unknown"
        }
