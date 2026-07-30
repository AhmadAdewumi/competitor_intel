# app/sse.py
# ============================================
# COMPETITORINTEL - Server-Sent Events
# ============================================

from flask import Response, stream_with_context
import queue
import time
import json
from typing import Dict, Any

subscribers = {}


def subscribe(run_id: str):
    q = queue.Queue()
    subscribers[run_id] = q
    return q


def unsubscribe(run_id: str):
    if run_id in subscribers:
        del subscribers[run_id]


def publish(run_id: str, event_type: str, data: Dict[str, Any]):
    if run_id in subscribers:
        try:
            subscribers[run_id].put({
                'type': event_type,
                'data': data
            })
        except Exception:
            pass


def sse_stream(run_id: str):
    q = subscribe(run_id)
    try:
        while True:
            try:
                event = q.get(timeout=600)
                yield f"data: {json.dumps(event)}\n\n"
            except queue.Empty:
                yield f"data: {json.dumps({'type': 'ping'})}\n\n"
    except GeneratorExit:
        unsubscribe(run_id)
    except Exception:
        unsubscribe(run_id)


class TraceCollector:
    def __init__(self):
        self.run_id = None
        self.topic_id = None
        self.step_number = 0

    def start_run(self, run_id: str, topic_id: int):
        self.run_id = run_id
        self.topic_id = topic_id
        self.step_number = 0
        publish(run_id, 'start', {'topic_id': topic_id, 'run_id': run_id})

    def log(self, agent: str, action: str, content: str = ''):
        if not self.run_id:
            return

        self.step_number += 1

        from .db import add_trace
        add_trace(
            self.run_id,
            self.topic_id,
            self.step_number,
            agent,
            action,
            content
        )

        publish(self.run_id, 'trace', {
            'step_number': self.step_number,
            'agent': agent,
            'action': action,
            'content': content[:200] if content else '',
            'timestamp': time.strftime('%H:%M:%S')
        })

    def complete(self, status: str = 'success', message: str = ''):
        if self.run_id:
            publish(self.run_id, 'complete', {
                'status': status,
                'message': message
            })

    def error(self, message: str):
        if self.run_id:
            publish(self.run_id, 'error', {'message': message})


trace_collector = TraceCollector()