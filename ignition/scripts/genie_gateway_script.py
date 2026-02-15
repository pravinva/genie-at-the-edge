#!/usr/bin/env python
"""
Genie Gateway Script for Ignition
Runs inside Ignition Gateway - no external proxy needed!

This script should be added to Ignition Designer:
1. Project → Scripts → Add Python Module
2. Name: genie_api
3. Paste this code
4. Save

Then call from Perspective views or other scripts:
    result = shared.genie_api.queryGenie("What is the status?")
"""

import system
import time

# Configuration - Update these values for your workspace
WORKSPACE_URL = "https://e2-demo-field-eng.cloud.databricks.com"
SPACE_ID = "01f10a2ce1831ea28203c2a6ce271590"

# Cache for OAuth tokens (module-level variables persist in gateway)
_token_cache = {
    'token': None,
    'expires_at': 0
}

# Cache for responses (5 minute TTL)
_response_cache = {}
CACHE_TTL = 300  # seconds


def _get_databricks_token():
    """
    Get OAuth token from Databricks CLI
    Uses module-level cache to avoid repeated CLI calls
    """
    import time

    # Check cache
    current_time = time.time()
    if _token_cache['token'] and current_time < _token_cache['expires_at']:
        return _token_cache['token']

    # Get fresh token
    try:
        cmd = ['databricks', 'auth', 'token', '--host', WORKSPACE_URL]
        result = system.util.execute(cmd, timeout=5000)  # 5 second timeout

        if not result:
            raise Exception("Empty response from databricks CLI")

        token_data = system.util.jsonDecode(result)
        token = token_data.get('access_token')

        if not token:
            raise Exception("No access_token in response")

        # Cache for 50 minutes (tokens valid for 1 hour)
        _token_cache['token'] = token
        _token_cache['expires_at'] = current_time + 3000

        return token

    except Exception as e:
        system.util.getLogger("genie_api").error("Failed to get token: " + str(e))
        raise Exception("Failed to get Databricks token: " + str(e))


def _get_cache_key(question, conversation_id):
    """Generate cache key from question and conversation ID"""
    import hashlib
    key = "{}:{}".format(question, conversation_id or 'new')
    return hashlib.md5(key.encode()).hexdigest()


def _get_cached_response(cache_key):
    """Get cached response if available and not expired"""
    current_time = time.time()
    if cache_key in _response_cache:
        cached_response, timestamp = _response_cache[cache_key]
        if current_time - timestamp < CACHE_TTL:
            return cached_response
        else:
            # Expired, remove from cache
            del _response_cache[cache_key]
    return None


def _set_cached_response(cache_key, response):
    """Cache a response"""
    _response_cache[cache_key] = (response, time.time())

    # Limit cache size to 100 entries
    if len(_response_cache) > 100:
        # Remove oldest entry
        oldest_key = min(_response_cache.keys(), key=lambda k: _response_cache[k][1])
        del _response_cache[oldest_key]


def queryGenie(question, conversationId=None):
    """
    Query Databricks Genie API

    Args:
        question (str): Natural language question to ask Genie
        conversationId (str, optional): Conversation ID for follow-up questions

    Returns:
        dict: {
            'success': bool,
            'response': str,
            'conversationId': str,
            'suggestedQuestions': list,
            'chartData': dict or None
        }

    Example:
        result = queryGenie("What is the current status of all equipment?")
        print(result['response'])

        # Follow-up question
        result2 = queryGenie("Show me details", conversationId=result['conversationId'])
    """
    logger = system.util.getLogger("genie_api")

    try:
        # Check cache for non-conversational queries
        if not conversationId:
            cache_key = _get_cache_key(question, conversationId)
            cached = _get_cached_response(cache_key)
            if cached:
                logger.info("Cache hit for query: " + question[:50])
                return cached

        # Get OAuth token
        token = _get_databricks_token()

        # Determine endpoint
        if conversationId:
            url = "{}/api/2.0/genie/spaces/{}/conversations/{}/messages".format(
                WORKSPACE_URL, SPACE_ID, conversationId
            )
        else:
            url = "{}/api/2.0/genie/spaces/{}/start-conversation".format(
                WORKSPACE_URL, SPACE_ID
            )

        # Prepare request
        headers = {
            "Authorization": "Bearer {}".format(token),
            "Content-Type": "application/json"
        }

        post_data = system.util.jsonEncode({"content": question})

        # Submit question to Genie
        logger.info("Submitting query to Genie: " + question[:50])
        response = system.net.httpPost(
            url=url,
            postData=post_data,
            headerValues=headers,
            timeout=30000  # 30 second timeout
        )

        # Parse initial response
        initial_data = system.util.jsonDecode(response)
        message_id = initial_data.get('message_id') or initial_data.get('message', {}).get('id')
        new_conversation_id = initial_data.get('conversation_id')

        if not message_id or not new_conversation_id:
            raise Exception("Failed to get message_id or conversation_id from Genie")

        # Poll for completion (Genie is async)
        logger.info("Polling for response (message_id: {})".format(message_id))
        response_text = None
        suggested_questions = []
        chart_data = None
        max_attempts = 60  # 30 seconds max with 500ms polling

        for attempt in range(max_attempts):
            # Poll immediately on first attempt, then wait
            if attempt > 0:
                time.sleep(0.5)  # 500ms polling interval

            # Get message status
            poll_url = "{}/api/2.0/genie/spaces/{}/conversations/{}/messages/{}".format(
                WORKSPACE_URL, SPACE_ID, new_conversation_id, message_id
            )

            poll_response = system.net.httpGet(
                url=poll_url,
                headerValues=headers,
                timeout=10000
            )

            message_status = system.util.jsonDecode(poll_response)
            status = message_status.get('status')

            if status == 'COMPLETED':
                logger.info("Query completed successfully")

                # Extract response from attachments
                attachments = message_status.get('attachments', [])
                result_text = []
                sql_query = None
                statement_id = None

                for attachment in attachments:
                    # Text response
                    if 'text' in attachment:
                        text_content = attachment.get('text', {}).get('content', '')
                        if text_content:
                            result_text.append(text_content)

                    # SQL query
                    elif 'query' in attachment:
                        query = attachment.get('query', {})
                        sql_query = query.get('query', '')
                        statement_id = query.get('statement_id')

                    # Suggested questions
                    elif 'suggested_questions' in attachment:
                        suggested_questions = attachment.get('suggested_questions', {}).get('questions', [])

                # Check if we should fetch chart data
                if statement_id and sql_query:
                    query_lower = sql_query.lower()
                    is_chart_worthy = (
                        ('order by' in query_lower or 'group by' in query_lower) and
                        any(kw in query_lower for kw in ['avg', 'sum', 'count', 'trend', 'over time', 'window_start', 'timestamp', 'date'])
                    )

                    if is_chart_worthy:
                        try:
                            chart_data = _fetch_chart_data(statement_id, sql_query, headers)
                        except Exception as e:
                            logger.warn("Could not fetch chart data: " + str(e))

                # Build response text
                if result_text:
                    response_text = '\n\n'.join(result_text)
                else:
                    response_text = message_status.get('content', 'Query completed but no results returned')

                break

            elif status == 'FAILED':
                error_msg = message_status.get('error', 'Unknown error')
                response_text = "Query failed: {}".format(error_msg)
                logger.error(response_text)
                break

        if response_text is None:
            response_text = "Query timed out after 30 seconds. Please try again."
            logger.warn(response_text)

        # Build final response
        result = {
            'success': True,
            'response': response_text,
            'conversationId': new_conversation_id or conversationId,
            'suggestedQuestions': suggested_questions,
            'chartData': chart_data
        }

        # Cache non-conversational queries
        if not conversationId:
            cache_key = _get_cache_key(question, conversationId)
            _set_cached_response(cache_key, result)

        return result

    except Exception as e:
        logger.error("Error querying Genie: " + str(e))
        return {
            'success': False,
            'response': "Error: {}".format(str(e)),
            'conversationId': conversationId,
            'suggestedQuestions': [],
            'chartData': None
        }


def _fetch_chart_data(statement_id, sql_query, headers):
    """Fetch SQL result data for charting"""
    result_url = "{}/api/2.0/sql/statements/{}/result/chunks/0".format(
        WORKSPACE_URL, statement_id
    )

    result_response = system.net.httpGet(
        url=result_url,
        headerValues=headers,
        timeout=10000
    )

    result_data = system.util.jsonDecode(result_response)
    rows = result_data.get('data_array', [])

    if not rows or len(rows[0]) < 2:
        return None

    # Extract column names from SQL SELECT clause
    columns = ['Column_{}'.format(i) for i in range(len(rows[0]))]

    # Try to parse column names from SQL
    import re
    select_match = re.search(r'SELECT\s+(.+?)\s+FROM', sql_query, re.IGNORECASE | re.DOTALL)
    if select_match:
        select_clause = select_match.group(1)
        col_parts = [p.strip() for p in select_clause.split(',')]
        for i, part in enumerate(col_parts[:len(columns)]):
            # Look for AS alias
            as_match = re.search(r'\s+AS\s+[`"]?(\w+)[`"]?', part, re.IGNORECASE)
            if as_match:
                columns[i] = as_match.group(1)
            else:
                # Use last word
                words = re.findall(r'[`"]?(\w+)[`"]?', part)
                if words:
                    columns[i] = words[-1]

    return {
        'columns': columns,
        'rows': rows
    }


# Test function
def testQuery():
    """
    Test the Genie API connection
    Run this from Script Console to verify setup
    """
    logger = system.util.getLogger("genie_api")
    logger.info("Testing Genie API connection...")

    result = queryGenie("What is the current status?")

    logger.info("Test result:")
    logger.info("  Success: " + str(result['success']))
    logger.info("  Response: " + result['response'][:100])
    logger.info("  Conversation ID: " + str(result['conversationId']))

    return result
