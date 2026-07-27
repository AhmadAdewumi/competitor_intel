# run_web.py
# ============================================
# COMPETITORINTEL - Web Application Runner
# ============================================

import os
from app import create_app

app = create_app()

if __name__ == "__main__":
    # Use environment variables for production
    debug = os.environ.get("DEBUG", "False").lower() == "true"
    port = int(os.environ.get("PORT", 5000))
    host = os.environ.get("HOST", "0.0.0.0")

    print("========================================")
    print("  CompetitorIntel Web Dashboard")
    print("========================================")
    print(f"  Running on: http://{host}:{port}")
    print("  Press Ctrl+C to stop")
    print("========================================")
    app.run(host=host, port=port, debug=debug, threaded=True)
