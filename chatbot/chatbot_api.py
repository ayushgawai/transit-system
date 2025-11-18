"""
Chatbot API for Transit Service Reliability & Demand Planning System

This Flask API provides natural language query interface to the Snowflake data warehouse.
Uses OpenAI GPT-3.5-turbo (free tier) or local LLM to answer questions about transit data.
"""

from flask import Flask, request, jsonify
import snowflake.connector
import os
from typing import Dict, Any, Optional
import json
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configuration from environment variables
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
SNOWFLAKE_ACCOUNT = os.environ.get("SNOWFLAKE_ACCOUNT")
SNOWFLAKE_USER = os.environ.get("SNOWFLAKE_USER")
SNOWFLAKE_PASSWORD = os.environ.get("SNOWFLAKE_PASSWORD")

# OpenAI client (supports both old and new API)
try:
    # Try new OpenAI client (v1.0+)
    from openai import OpenAI
    openai_client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None
    OPENAI_NEW_API = True
except ImportError:
    # Fallback to old OpenAI API (v0.x)
    try:
        import openai
        if OPENAI_API_KEY:
            openai.api_key = OPENAI_API_KEY
        openai_client = openai
        OPENAI_NEW_API = False
    except ImportError:
        openai_client = None
        OPENAI_NEW_API = False
        logger.warning("OpenAI library not installed. Chatbot will not work.")


# System prompt for the chatbot
SYSTEM_PROMPT = """You are a transit analytics assistant. You help users query and analyze transit service reliability, demand forecasting, crowding, and revenue data from a Snowflake data warehouse.

Available tables and schemas:
- ANALYTICS.RELIABILITY_METRICS: On-time performance, delays, headway gaps, reliability scores
- ANALYTICS.DEMAND_METRICS: Boardings, demand intensity by route/stop/time
- ANALYTICS.CROWDING_METRICS: Occupancy ratios, crowding percentages
- ANALYTICS.REVENUE_METRICS: Estimated revenue, revenue loss, revenue opportunities
- ANALYTICS.DECISION_SUPPORT: Ranked recommendations for fleet reallocation, frequency adjustments
- ML.FORECASTS: ML predictions for demand, delays, crowding (next 24-48 hours)
- STAGING.STG_ALERTS: Service alerts and disruptions

When users ask questions:
1. Translate the natural language question into a Snowflake SQL query
2. Execute the query and return results
3. Provide a clear, concise answer with insights

Common question types:
- "Which route tomorrow at 8am is likely to be most crowded?" → Query ML.FORECASTS for crowding forecasts at 8am
- "What's the on-time performance for Route 1 this week?" → Query ANALYTICS.RELIABILITY_METRICS
- "Which stops have the highest boarding rates?" → Query ANALYTICS.DEMAND_METRICS
- "Recommend fleet reallocation for tomorrow's morning rush" → Query ANALYTICS.DECISION_SUPPORT and ML.FORECASTS
- "Show me revenue impact of delays on Route 5" → Query ANALYTICS.REVENUE_METRICS

Always format SQL queries clearly and explain results in plain language."""


def get_snowflake_connection():
    """Create Snowflake connection."""
    return snowflake.connector.connect(
        account=SNOWFLAKE_ACCOUNT,
        user=SNOWFLAKE_USER,
        password=SNOWFLAKE_PASSWORD,
        warehouse=os.environ.get("SNOWFLAKE_WAREHOUSE", "TRANSIT_WH"),
        database=os.environ.get("SNOWFLAKE_DATABASE", "TRANSIT_DB"),
        schema="ANALYTICS",
        role=os.environ.get("SNOWFLAKE_ROLE", "TRANSIT_ROLE")
    )


def generate_sql_query(user_question: str) -> str:
    """
    Use OpenAI to generate SQL query from natural language question.
    
    Args:
        user_question: Natural language question
        
    Returns:
        SQL query string
    """
    if not openai_client:
        raise ValueError("OpenAI client not initialized. Check OPENAI_API_KEY environment variable.")
    
    try:
        if OPENAI_NEW_API:
            # New OpenAI API (v1.0+)
            response = openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"Translate this question into a Snowflake SQL query: {user_question}"}
                ],
                temperature=0.3,
                max_tokens=500
            )
            sql_query = response.choices[0].message.content.strip()
        else:
            # Old OpenAI API (v0.x)
            response = openai_client.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"Translate this question into a Snowflake SQL query: {user_question}"}
                ],
                temperature=0.3,
                max_tokens=500
            )
            sql_query = response.choices[0].message.content.strip()
        
        # Extract SQL query if wrapped in code blocks
        if "```sql" in sql_query:
            sql_query = sql_query.split("```sql")[1].split("```")[0].strip()
        elif "```" in sql_query:
            sql_query = sql_query.split("```")[1].split("```")[0].strip()
        
        logger.info(f"Generated SQL query: {sql_query}")
        return sql_query
        
    except Exception as e:
        logger.error(f"Error generating SQL query: {str(e)}")
        raise


def execute_sql_query(sql_query: str) -> list:
    """
    Execute SQL query in Snowflake and return results.
    
    Args:
        sql_query: SQL query string
        
    Returns:
        List of dictionaries (rows as dicts)
    """
    conn = get_snowflake_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(sql_query)
        results = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        
        # Convert to list of dictionaries
        rows = []
        for row in results:
            rows.append(dict(zip(columns, row)))
        
        logger.info(f"Query executed successfully: {len(rows)} rows returned")
        return rows
        
    except Exception as e:
        logger.error(f"Error executing SQL query: {str(e)}")
        raise
    finally:
        cursor.close()
        conn.close()


def format_answer(user_question: str, sql_query: str, results: list) -> str:
    """
    Format query results into natural language answer.
    
    Args:
        user_question: Original user question
        sql_query: SQL query that was executed
        results: Query results
        
    Returns:
        Formatted answer string
    """
    if not openai_client:
        # Fallback if OpenAI not available
        if results:
            return f"Query returned {len(results)} results. Here are the top results: {json.dumps(results[:5], default=str, indent=2)}"
        else:
            return "Query returned no results."
    
    try:
        results_json = json.dumps(results, default=str)
        
        if OPENAI_NEW_API:
            # New OpenAI API (v1.0+)
            response = openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"""User asked: {user_question}

SQL query executed: {sql_query}

Query results:
{results_json}

Please provide a clear, concise answer to the user's question based on these results. Include specific numbers and insights."""}
                ],
                temperature=0.3,
                max_tokens=500
            )
            answer = response.choices[0].message.content.strip()
        else:
            # Old OpenAI API (v0.x)
            response = openai_client.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"""User asked: {user_question}

SQL query executed: {sql_query}

Query results:
{results_json}

Please provide a clear, concise answer to the user's question based on these results. Include specific numbers and insights."""}
                ],
                temperature=0.3,
                max_tokens=500
            )
            answer = response.choices[0].message.content.strip()
        
        logger.info(f"Formatted answer generated")
        return answer
        
    except Exception as e:
        logger.error(f"Error formatting answer: {str(e)}")
        # Fallback to simple formatting
        if results:
            return f"Query returned {len(results)} results. Here are the top results: {json.dumps(results[:5], default=str, indent=2)}"
        else:
            return "Query returned no results."


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint."""
    return jsonify({"status": "healthy", "timestamp": datetime.utcnow().isoformat()})


@app.route("/query", methods=["POST"])
def query():
    """
    Process natural language query.
    
    Request body:
    {
        "question": "Which route tomorrow at 8am is likely to be most crowded?",
        "include_sql": false  // Optional: include SQL query in response
    }
    """
    try:
        data = request.get_json()
        user_question = data.get("question", "")
        include_sql = data.get("include_sql", False)
        
        if not user_question:
            return jsonify({"error": "Question is required"}), 400
        
        # Generate SQL query
        sql_query = generate_sql_query(user_question)
        
        # Execute query
        results = execute_sql_query(sql_query)
        
        # Format answer
        answer = format_answer(user_question, sql_query, results)
        
        # Build response
        response = {
            "question": user_question,
            "answer": answer,
            "result_count": len(results),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if include_sql:
            response["sql_query"] = sql_query
            response["results"] = results
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/query/sql", methods=["POST"])
def query_sql():
    """
    Execute SQL query directly (for testing/debugging).
    
    Request body:
    {
        "sql": "SELECT * FROM MARTS.RELIABILITY_METRICS LIMIT 10"
    }
    """
    try:
        data = request.get_json()
        sql_query = data.get("sql", "")
        
        if not sql_query:
            return jsonify({"error": "SQL query is required"}), 400
        
        # Execute query
        results = execute_sql_query(sql_query)
        
        return jsonify({
            "sql": sql_query,
            "results": results,
            "result_count": len(results),
            "timestamp": datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error executing SQL: {str(e)}")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    # Run Flask app
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)

