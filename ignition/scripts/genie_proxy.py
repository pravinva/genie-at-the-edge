#!/usr/bin/env python3
"""
Genie API Proxy Server for Ignition
Handles CORS and token management for Databricks Genie Conversation API calls
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import urllib.request
import urllib.error
import subprocess
import sys
import os
import time

# Databricks Configuration
WORKSPACE_URL = "https://e2-demo-field-eng.cloud.databricks.com"
SPACE_ID = "01f10a2ce1831ea28203c2a6ce271590"

def get_databricks_token():
    """Get fresh OAuth token from databricks CLI"""
    try:
        result = subprocess.run(
            ["databricks", "auth", "token", "--host", WORKSPACE_URL],
            capture_output=True,
            text=True,
            check=True
        )
        token_data = json.loads(result.stdout)
        return token_data["access_token"]
    except Exception as e:
        print(f"Error getting token: {e}", file=sys.stderr)
        return None

class GenieProxyHandler(BaseHTTPRequestHandler):

    def do_OPTIONS(self):
        """Handle preflight CORS requests"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_POST(self):
        """Handle POST requests to Genie API"""

        if self.path == '/api/genie/query':
            try:
                # Read request body
                content_length = int(self.headers['Content-Length'])
                body = self.rfile.read(content_length)
                request_data = json.loads(body.decode('utf-8'))

                question = request_data.get('question', '')
                conversation_id = request_data.get('conversationId')

                if not question:
                    self.send_error(400, "Missing 'question' in request")
                    return

                # Get fresh token
                token = get_databricks_token()
                if not token:
                    self.send_error(500, "Failed to get authentication token")
                    return

                # Determine endpoint
                if conversation_id:
                    endpoint = f"{WORKSPACE_URL}/api/2.0/genie/spaces/{SPACE_ID}/conversations/{conversation_id}/messages"
                else:
                    endpoint = f"{WORKSPACE_URL}/api/2.0/genie/spaces/{SPACE_ID}/start-conversation"

                # Prepare request to Databricks
                genie_request = urllib.request.Request(
                    endpoint,
                    data=json.dumps({"content": question}).encode('utf-8'),
                    headers={
                        'Authorization': f'Bearer {token}',
                        'Content-Type': 'application/json'
                    },
                    method='POST'
                )

                # Call Databricks Genie API (submit question)
                with urllib.request.urlopen(genie_request) as response:
                    genie_response = json.loads(response.read().decode('utf-8'))

                print(f"DEBUG - Initial Genie Response: {json.dumps(genie_response, indent=2)}", file=sys.stderr)

                # Extract message and conversation IDs
                message_id = genie_response.get('message_id') or genie_response.get('message', {}).get('id')
                new_conversation_id = genie_response.get('conversation_id')

                if not message_id or not new_conversation_id:
                    raise Exception("Failed to get message_id or conversation_id from Genie")

                # Poll for the actual response (Genie processes asynchronously)
                print(f"⏳ Polling for response (message_id: {message_id})...", file=sys.stderr)
                response_text = None
                max_attempts = 30  # 30 seconds max

                for attempt in range(max_attempts):
                    time.sleep(1)  # Wait 1 second between polls

                    # Get message status
                    poll_url = f"{WORKSPACE_URL}/api/2.0/genie/spaces/{SPACE_ID}/conversations/{new_conversation_id}/messages/{message_id}"
                    poll_request = urllib.request.Request(
                        poll_url,
                        headers={'Authorization': f'Bearer {token}'},
                        method='GET'
                    )

                    with urllib.request.urlopen(poll_request) as poll_response:
                        message_status = json.loads(poll_response.read().decode('utf-8'))

                    status = message_status.get('status')
                    print(f"  Poll {attempt+1}: status={status}", file=sys.stderr)

                    if status == 'COMPLETED':
                        print(f"DEBUG - Completed message: {json.dumps(message_status, indent=2)}", file=sys.stderr)
                        # Get the attachments (SQL results, charts, etc)
                        attachments = message_status.get('attachments', [])

                        # Extract response from attachments
                        result_text = []
                        sql_query = None
                        suggested_questions = []
                        chart_data = None
                        statement_id = None

                        for attachment in attachments:
                            # Text response from Genie
                            if 'text' in attachment:
                                text_content = attachment.get('text', {}).get('content', '')
                                if text_content:
                                    result_text.append(text_content)

                            # SQL query that was executed
                            elif 'query' in attachment:
                                query = attachment.get('query', {})
                                sql_query = query.get('query', '')
                                statement_id = query.get('statement_id')

                            # Suggested follow-up questions
                            elif 'suggested_questions' in attachment:
                                suggested_questions = attachment.get('suggested_questions', {}).get('questions', [])

                        # If we have a statement_id and query looks like time series, fetch data for charting
                        query_lower = sql_query.lower() if sql_query else ''
                        is_chart_worthy = (
                            statement_id and
                            ('order by' in query_lower or 'group by' in query_lower) and
                            any(kw in query_lower for kw in ['avg', 'sum', 'count', 'trend', 'over time', 'window_start', 'timestamp', 'date'])
                        )
                        print(f"DEBUG - Chart worthy check: statement_id={statement_id}, is_chart_worthy={is_chart_worthy}", file=sys.stderr)
                        if is_chart_worthy:
                            try:
                                # Fetch query results
                                result_url = f"{WORKSPACE_URL}/api/2.0/sql/statements/{statement_id}/result/chunks/0"
                                print(f"DEBUG - Fetching chart data from: {result_url}", file=sys.stderr)
                                result_request = urllib.request.Request(
                                    result_url,
                                    headers={'Authorization': f'Bearer {token}'},
                                    method='GET'
                                )
                                with urllib.request.urlopen(result_request) as result_response:
                                    result_data = json.loads(result_response.read().decode('utf-8'))
                                    print(f"DEBUG - Got result data with {len(result_data.get('data_array', []))} rows", file=sys.stderr)

                                    # Extract data rows - they're already in the right format
                                    rows = result_data.get('data_array', [])

                                    # Column names: SQL results API doesn't return schema
                                    # Infer from the query SELECT clause if possible
                                    columns = []
                                    if rows and len(rows[0]) >= 2:
                                        # Default column names based on position
                                        columns = [f'Column_{i}' for i in range(len(rows[0]))]

                                        # Try to extract better names from SQL query
                                        import re
                                        select_match = re.search(r'SELECT\s+(.+?)\s+FROM', sql_query, re.IGNORECASE | re.DOTALL)
                                        if select_match:
                                            select_clause = select_match.group(1)
                                            # Extract column aliases (AS name) or expressions
                                            col_parts = [p.strip() for p in select_clause.split(',')]
                                            for i, part in enumerate(col_parts[:len(columns)]):
                                                # Look for AS alias
                                                as_match = re.search(r'\s+AS\s+[`"]?(\w+)[`"]?', part, re.IGNORECASE)
                                                if as_match:
                                                    columns[i] = as_match.group(1)
                                                # Or use last word/identifier
                                                else:
                                                    words = re.findall(r'[`"]?(\w+)[`"]?', part)
                                                    if words:
                                                        columns[i] = words[-1]

                                    print(f"DEBUG - Columns: {columns}", file=sys.stderr)

                                    print(f"DEBUG - Extracted {len(rows)} rows, {len(columns)} columns", file=sys.stderr)
                                    if rows and len(columns) >= 2:
                                        chart_data = {
                                            'columns': columns,
                                            'rows': rows
                                        }
                                        print(f"✓ Fetched {len(rows)} rows for charting", file=sys.stderr)
                                    else:
                                        print(f"DEBUG - Not enough data for chart: rows={len(rows)}, cols={len(columns)}", file=sys.stderr)
                            except Exception as e:
                                print(f"Warning: Could not fetch chart data: {e}", file=sys.stderr)
                                import traceback
                                traceback.print_exc(file=sys.stderr)

                        # Build the response
                        if result_text:
                            response_text = '\n\n'.join(result_text)
                            # Optionally include SQL if you want to show it
                            # if sql_query:
                            #     response_text += f"\n\n<details>\n<summary>SQL Query</summary>\n\n```sql\n{sql_query}\n```\n</details>"
                        else:
                            response_text = message_status.get('content', 'Query completed but no results returned')
                        break

                    elif status == 'FAILED':
                        response_text = f"Query failed: {message_status.get('error', 'Unknown error')}"
                        break

                if response_text is None:
                    response_text = "Query timed out after 30 seconds. Please try again."

                # Send response back to client
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()

                response_data = {
                    'success': True,
                    'response': response_text,
                    'conversationId': new_conversation_id or conversation_id,
                    'suggestedQuestions': suggested_questions,
                    'chartData': chart_data
                }
                self.wfile.write(json.dumps(response_data).encode('utf-8'))

                print(f"✓ Processed query: {question[:50]}...", file=sys.stderr)

            except urllib.error.HTTPError as e:
                error_body = e.read().decode('utf-8')
                print(f"Databricks API Error: {e.code} - {error_body}", file=sys.stderr)
                self.send_error(502, f"Databricks API error: {e.code}")

            except Exception as e:
                print(f"Proxy Error: {str(e)}", file=sys.stderr)
                self.send_error(500, f"Internal proxy error: {str(e)}")

        else:
            self.send_error(404, "Endpoint not found")

    def log_message(self, format, *args):
        """Custom logging"""
        sys.stderr.write(f"[{self.log_date_time_string()}] {format % args}\n")

def run_proxy(port=8185):
    """Start the proxy server"""
    server_address = ('', port)
    httpd = HTTPServer(server_address, GenieProxyHandler)

    print(f"🚀 Genie Proxy Server running on http://localhost:{port}")
    print(f"   Workspace: {WORKSPACE_URL}")
    print(f"   Space ID: {SPACE_ID}")
    print(f"   Proxy endpoint: http://localhost:{port}/api/genie/query")
    print(f"\nPress Ctrl+C to stop\n")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\n⚠ Shutting down proxy server...")
        httpd.shutdown()

if __name__ == '__main__':
    port = int(os.environ.get('PROXY_PORT', 8185))
    run_proxy(port)
