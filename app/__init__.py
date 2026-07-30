# app/__init__.py
# ============================================
# COMPETITORINTEL - Flask Application
# ============================================

import os
import threading
from datetime import datetime

from flask import (
    Flask,
    Response,
    jsonify,
    render_template,
    request,
    send_from_directory,
    stream_with_context,
)
from flask_cors import CORS

from src.utils.logger import log

# Import database functions
from .db import (
    complete_report,
    create_report,
    create_topic,
    delete_topic,
    get_all_topics,
    get_latest_report,
    get_llm_provider,
    get_reports_for_topic,
    get_setting,
    get_topic,
    get_traces,
    init_db,
    set_llm_provider,
    set_setting,
    update_topic,
)
from .sse import sse_stream, trace_collector


def create_app():
    """Create and configure the Flask application."""
    # Initialize database
    init_db()

    # Create Flask app
    app = Flask(
        __name__,
        static_folder='static',
        static_url_path='/static',
        template_folder='templates'
    )
    app.config['SECRET_KEY'] = 'competitor_intel_secret_key'
    CORS(app)

    # ============================================
    # MAIN PAGE
    # ============================================

    @app.route('/')
    def index():
        """Main dashboard."""
        return render_template('index.html')

    # ============================================
    # STATIC FILES
    # ============================================

    @app.route('/static/<path:filename>')
    def serve_static(filename):
        """Serve static files."""
        return send_from_directory('static', filename)

    # ============================================
    # TOPIC API ROUTES
    # ============================================

    @app.route('/api/topics', methods=['GET'])
    def api_topics():
        """Get all topics."""
        try:
            topics = get_all_topics()
            for topic in topics:
                latest = get_latest_report(topic['id'])
                topic['latest_report'] = latest
            return jsonify({'topics': topics})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route("/api/publish_trace", methods=["POST"])
    def publish_trace():
        """Receive a trace from an agent and forward to SSE."""
        data = request.get_json()
        run_id = data.get("run_id")
        agent = data.get("agent", "System")
        action = data.get("action", "")
        content = data.get("content", "")

        if run_id:
            from .sse import publish

            publish(
                run_id,
                "trace",
                {
                    "agent": agent,
                    "action": action,
                    "content": content,
                    "timestamp": datetime.now().strftime("%H:%M:%S"),
                },
            )

        return jsonify({"success": True})

    @app.route('/api/topics/<int:topic_id>', methods=['GET'])
    def api_topic(topic_id):
        """Get a single topic."""
        topic = get_topic(topic_id)
        if not topic:
            return jsonify({'error': 'Topic not found'}), 404
        return jsonify({'topic': topic})

    @app.route('/api/topics', methods=['POST'])
    def api_create_topic():
        """Create a new topic."""
        data = request.get_json()
        if not data.get('name'):
            return jsonify({'error': 'Name is required'}), 400
        topic_id = create_topic(data)
        return jsonify({'id': topic_id, 'success': True}), 201

    @app.route('/api/topics/<int:topic_id>', methods=['PUT'])
    def api_update_topic(topic_id):
        """Update a topic."""
        data = request.get_json()
        if update_topic(topic_id, data):
            return jsonify({'success': True})
        return jsonify({'error': 'Topic not found'}), 404

    @app.route('/api/topics/<int:topic_id>', methods=['DELETE'])
    def api_delete_topic(topic_id):
        """Delete a topic."""
        if delete_topic(topic_id):
            return jsonify({'success': True})
        return jsonify({'error': 'Topic not found'}), 404

    # ============================================
    # REPORT DOWNLOAD
    # ============================================

    @app.route("/api/topics/<int:topic_id>/report")
    def api_download_report(topic_id):
        """Download a report for a topic."""
        import glob
        import os
        import tempfile
        from datetime import datetime

        from flask import Response, send_file

        # FIRST: Try to get from database
        reports = get_reports_for_topic(topic_id, 1)

        content = None
        topic_name = None
        topic = get_topic(topic_id)
        topic_name = topic.get("name", "report") if topic else "report"
        safe_name = topic_name.lower().replace(" ", "_").replace("/", "_")

        if reports:
            report = reports[0]
            content = report.get("content", "")

        # SECOND: If not in database, look for files in reports/ folder
        if not content:
            # Find the most recent report file for this topic
            report_files = glob.glob(f"reports/{safe_name}*.md")
            if report_files:
                latest = max(report_files, key=os.path.getmtime)
                with open(latest, "r") as f:
                    content = f.read()
                    log.info(f"Found report file: {latest}")

        if not content:
            return jsonify({"error": "No report found for this topic"}), 404

        format_type = request.args.get("format", "md")
        date_str = datetime.now().strftime("%Y%m%d")

        # Generate different formats
        if format_type == "md":
            filename = f"{safe_name}_{date_str}.md"
            return Response(
                content,
                mimetype="text/markdown",
                headers={"Content-Disposition": f'attachment; filename="{filename}"'},
            )

        elif format_type == "html":
            from src.utils.report_formatter import generate_html_report

            html_content = generate_html_report(content, topic_name)
            filename = f"{safe_name}_{date_str}.html"
            return Response(
                html_content,
                mimetype="text/html",
                headers={"Content-Disposition": f'attachment; filename="{filename}"'},
            )

        elif format_type == "pdf":
            from src.utils.report_formatter import generate_html_report, save_pdf

            html_content = generate_html_report(content, topic_name)
            filename = f"{safe_name}_{date_str}.pdf"

            # Generate PDF to temp file
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                save_pdf(html_content, tmp.name)
                tmp_path = tmp.name

            # Send the file and clean up
            response = send_file(tmp_path, as_attachment=True, download_name=filename)

            # Clean up temp file after sending
            def cleanup():
                try:
                    os.unlink(tmp_path)
                except:
                    pass

            response.call_on_close(cleanup)
            return response

        else:
            return jsonify({"error": f"Invalid format: {format_type}"}), 400

    # ============================================
    # RUN TOPIC
    # ============================================

    @app.route("/api/topics/<int:topic_id>/run", methods=["POST"])
    def api_run_topic(topic_id):
        """Run a topic and stream traces."""
        topic = get_topic(topic_id)
        if not topic:
            return jsonify({"error": "Topic not found"}), 404

        # Generate run_id
        run_id = f"run_{topic_id}_{int(datetime.now().timestamp())}"
        trace_collector.start_run(run_id, topic_id)

        def run_in_background():
            try:
                # FIX 1: Set the CURRENT_RUN_ID so runner.py uses the SAME ID
                os.environ["CURRENT_RUN_ID"] = run_id

                from src.runner import TopicRunner

                runner = TopicRunner()
                result = runner.run_topic(topic)
                trace_collector.complete("success", "Report generated successfully")
            except Exception as e:
                # FIX 2: Print errors to terminal!
                import traceback

                from src.utils.logger import log

                log.error(f"Background thread crashed: {str(e)}")
                log.error(traceback.format_exc())

                # Send error to UI
                trace_collector.error(f"Agent Error: {str(e)}")

        thread = threading.Thread(target=run_in_background)
        thread.daemon = True
        thread.start()

        return jsonify({"run_id": run_id})

    # ============================================
    # SSE STREAM
    # ============================================

    @app.route("/api/stream/<run_id>")
    def api_stream(run_id):
        """SSE endpoint for traces."""
        return Response(
            stream_with_context(sse_stream(run_id)),
            mimetype="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",  # Disable nginx buffering
                "Connection": "keep-alive",
            },
        )

    # ============================================
    # TRACES
    # ============================================

    @app.route('/api/traces/<run_id>')
    def api_traces(run_id):
        """Get all traces for a run."""
        traces = get_traces(run_id)
        return jsonify({'traces': traces})

    # ============================================
    # REPORTS
    # ============================================

    @app.route('/api/topics/<int:topic_id>/reports')
    def api_reports(topic_id):
        """Get reports for a topic."""
        reports = get_reports_for_topic(topic_id)
        return jsonify({'reports': reports})

    # ============================================
    # SETTINGS
    # ============================================

    @app.route("/api/settings", methods=["GET"])
    def api_settings():
        """Get settings."""
        return jsonify(
            {
                "scheduler_enabled": get_setting("scheduler_enabled", "true") == "true",
                "email_enabled": get_setting("email_enabled", "true") == "true",
                "llm_provider": get_llm_provider(),
            }
        )

    @app.route("/api/settings", methods=["POST"])
    def api_update_settings():
        """Update settings."""
        data = request.get_json()

        # Handle llm_provider specifically
        if "llm_provider" in data:
            try:
                set_llm_provider(data["llm_provider"])
            except ValueError as e:
                return jsonify({"error": str(e)}), 400

        # Handle other settings
        for key, value in data.items():
            if key != "llm_provider":
                set_setting(key, str(value))

        return jsonify({"success": True})

    # ============================================
    # HEALTH CHECK
    # ============================================

    @app.route('/api/health')
    def api_health():
        """Health check."""
        return jsonify({'status': 'ok', 'app': 'competitor_intel'})

    return app

