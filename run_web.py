# run_web.py
# ============================================
# COMPETITORINTEL - Web Application Runner
# ============================================

from app import create_app

app = create_app()

if __name__ == '__main__':
    print("========================================")
    print("  CompetitorIntel Web Dashboard")
    print("========================================")
    print("  Open: http://localhost:5000")
    print("  Press Ctrl+C to stop")
    print("========================================")
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)