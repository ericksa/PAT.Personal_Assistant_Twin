#!/usr/bin/env python3
import requests
import sys

SERVICES = {
    "PAT Core (8010)": "http://localhost:8010/pat/health",
    "Ingest Service (8001)": "http://localhost:8001/health",
    "Agent Service (8002)": "http://localhost:8002/health",
    "MCP Server (8003)": "http://localhost:8003/health",
    "Manager (8888)": "http://localhost:8888/api/services",
    "Grafana (3001)": "http://localhost:3001/api/health",
    "Prometheus (9090)": "http://localhost:9090/-/healthy",
    "n8n (5678)": "http://localhost:5678/healthz",
}


def check_services():
    print("🔍 PAT System Health Check")
    print("-" * 30)
    all_ok = True
    for name, url in SERVICES.items():
        try:
            resp = requests.get(url, timeout=5)
            if resp.status_code < 400:
                print(f"✅ {name}: UP ({resp.status_code})")
            else:
                print(f"⚠️ {name}: DEGRADED ({resp.status_code})")
                all_ok = False
        except Exception as e:
            print(f"❌ {name}: DOWN")
            all_ok = False

    print("-" * 30)
    if all_ok:
        print("🎉 All systems nominal!")
    else:
        print("❌ Some services are down. Check Docker or main_pat.py logs.")
    return all_ok


if __name__ == "__main__":
    if not check_services():
        sys.exit(1)
