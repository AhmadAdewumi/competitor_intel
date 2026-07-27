# src/utils/trace.py
# ============================================
# TRACE PUBLISHER
# ============================================

import os
import requests
import threading


def get_trace_endpoint():
    """Get the trace endpoint from environment or use default."""
    # Use environment variable if set, otherwise fallback to localhost
    endpoint = os.environ.get('TRACE_ENDPOINT')
    if endpoint:
        return endpoint
    # For production Render, the app is served at the root
    # The endpoint is relative to the app's base URL
    return os.environ.get('BASE_URL', 'http://localhost:5000') + '/api/publish_trace'


def publish_trace(agent: str, action: str, content: str = ''):
    """Publish a trace to the dashboard."""
    run_id = os.environ.get('CURRENT_RUN_ID')
    if not run_id:
        return

    if len(content) > 200:
        content = content[:200] + '...'

    def send():
        try:
            endpoint = get_trace_endpoint()
            requests.post(
                endpoint,
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