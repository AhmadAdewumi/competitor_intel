# src/utils/trace.py
# ============================================
# TRACE PUBLISHER
# ============================================

import os
import requests
import threading


def publish_trace(agent: str, action: str, content: str = ''):
    """Publish a trace to the dashboard."""
    run_id = os.environ.get('CURRENT_RUN_ID')
    if not run_id:
        return

    if len(content) > 200:
        content = content[:200] + '...'

    def send():
        try:
            requests.post(
                'http://localhost:5000/api/publish_trace',
                json={
                    'run_id': run_id,
                    'agent': agent,
                    'action': action,
                    'content': content
                },
                timeout=1
            )
        except Exception:
            pass

    threading.Thread(target=send, daemon=True).start()