"""
Chat Handler
Main logic for processing user questions and generating responses
"""

import re
import json
from typing import Dict, Optional, List, Any
from .perplexity_client import PerplexityClient
from .schema_context import get_system_prompt, SCHEMA_CONTEXT

class ChatHandler:
    """Handles chat interactions with LLM and Snowflake"""
    
    def __init__(self, api_key: str, snowflake_conn=None):
        self.client = PerplexityClient(api_key=api_key)
        self.snowflake_conn = snowflake_conn
        self.conversation_history: List[Dict] = []
        self.max_history = 10  # Keep last 10 messages for context
    
    def process_message(self, user_message: str) -> Dict[str, Any]:
        """
        Process a user message and return a response
        
        Args:
            user_message: The user's question
            
        Returns:
            Dict with response, any data, and metadata
        """
        # Always assume questions are about transit data - don't reject
        # The system prompt will guide the LLM to answer transit-related questions
        
        query_data = None
        
        # Always generate SQL query for transit-related questions
        # First, determine if we need to query data
        needs_query = self._needs_data_query(user_message)
        
        if needs_query and self.snowflake_conn:
            # Generate SQL query first, then execute it, then answer
            sql_query = self._generate_sql_query(user_message)
            
            if sql_query:
                # Execute SQL query
                query_result = self._execute_sql(sql_query)
                
                if query_result["success"] and query_result["data"]:
                    query_data = query_result["data"]
                    # Build response based on actual data
                    response_text = self._generate_response_from_data(user_message, query_data)
                else:
                    # No data found
                    response_text = f"I checked the transit data, but no information was found for your question. This could mean:\n\n• The data hasn't been loaded yet\n• The specific route/stop you're asking about doesn't have data\n• The time period you're asking about has no records\n\nPlease try asking about a different route, stop, or time period, or check the admin panel to see what data is available."
            else:
                # Couldn't generate SQL, use LLM with context
                response_text = self._get_llm_response_with_context(user_message)
        else:
            # General question, use LLM with context
            response_text = self._get_llm_response_with_context(user_message)
        
        # Clean up any SQL that might have slipped through
        response_text = self._remove_sql_from_response(response_text)
        
        # Update conversation history
        self.conversation_history.append({"role": "user", "content": user_message})
        self.conversation_history.append({"role": "assistant", "content": response_text})
        
        return {
            "success": True,
            "response": response_text,
            "data": query_data,
            "sql": None  # Don't expose SQL to frontend
        }
    
    def _get_current_data_context(self) -> Optional[str]:
        """Fetch current metrics to provide as context to LLM"""
        if not self.snowflake_conn:
            return None
        
        try:
            from config.warehouse_config import get_warehouse_config
            config = get_warehouse_config()
            snowflake_config = config.get_snowflake_config()
            database = snowflake_config.get('database', 'USER_DB_HORNET')
            
            cursor = self.snowflake_conn.cursor()
            context_parts = []
            
            # Get route summary from GTFS routes
            cursor.execute(f"""
                SELECT 
                    r.ROUTE_LONG_NAME,
                    r.ROUTE_SHORT_NAME,
                    r.AGENCY,
                    COUNT(DISTINCT st.STOP_ID) as STOP_COUNT
                FROM {database}.RAW.STG_GTFS_ROUTES r
                INNER JOIN {database}.RAW.STG_GTFS_TRIPS t ON r.ROUTE_ID = t.ROUTE_ID
                INNER JOIN {database}.RAW.STG_GTFS_STOP_TIMES st ON t.TRIP_ID = st.TRIP_ID
                GROUP BY r.ROUTE_LONG_NAME, r.ROUTE_SHORT_NAME, r.AGENCY
                ORDER BY STOP_COUNT DESC
                LIMIT 10
            """)
            rows = cursor.fetchall()
            if rows:
                context_parts.append("TOP ROUTES BY STOPS:")
                for row in rows:
                    route_long, route_short, agency, stops = row
                    route_name = route_long or route_short or "Unknown"
                    context_parts.append(f"  {route_name} ({agency}): {stops} stops")
            
            # Get streaming data summary
            cursor.execute(f"""
                SELECT 
                    AGENCY,
                    COUNT(*) as TOTAL,
                    COUNT(CASE WHEN DELAY_SECONDS IS NOT NULL AND DELAY_SECONDS > 0 THEN 1 END) as DELAYED,
                    AVG(CASE WHEN DELAY_SECONDS IS NOT NULL AND DELAY_SECONDS > 0 THEN DELAY_SECONDS END) as AVG_DELAY_SEC
                FROM {database}.LANDING.LANDING_STREAMING_DEPARTURES
                WHERE CONSUMED_AT >= DATEADD(day, -7, CURRENT_TIMESTAMP())
                GROUP BY AGENCY
            """)
            rows = cursor.fetchall()
            if rows:
                context_parts.append("\nSTREAMING DATA (Last 7 days):")
                for row in rows:
                    agency, total, delayed, avg_delay = row
                    delay_pct = (delayed / total * 100) if total > 0 else 0
                    avg_delay_min = (avg_delay / 60) if avg_delay else 0
                    context_parts.append(f"  {agency}: {total} total, {delayed} delayed ({delay_pct:.1f}%), avg delay {avg_delay_min:.1f} min")
            
            cursor.close()
            return "\n".join(context_parts)
            
        except Exception as e:
            print(f"Error getting data context: {e}")
            return None
    
    def _remove_sql_from_response(self, text: str) -> str:
        """Remove SQL queries and follow-up questions from the response"""
        import re
        
        # Remove SQL code blocks
        text = re.sub(r'```sql\n.*?\n```', '', text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'```\n?SELECT.*?```', '', text, flags=re.DOTALL | re.IGNORECASE)
        
        # Remove inline SQL
        text = re.sub(r'`SELECT[^`]+`', '', text, flags=re.IGNORECASE)
        
        # Remove phrases about running queries and follow-up questions
        phrases_to_remove = [
            r"Here is the SQL query.*?:",
            r"I will query.*?\.",
            r"Let me (run|execute|query|check).*?\.",
            r"Would you like me to.*?\?",
            r"Should I (run|execute|fetch|provide).*?\?",
            r"I can (query|provide|fetch).*?\.",
            r"Let me know if.*\.",
            r"If you (want|need|would like).*\?",
            r"Do you want me to.*\?",
        ]
        for phrase in phrases_to_remove:
            text = re.sub(phrase, '', text, flags=re.IGNORECASE)
        
        # Remove trailing questions asking for confirmation
        text = re.sub(r'\n\n.*would you like.*\?$', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\n\n.*do you want.*\?$', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\n\n.*shall I.*\?$', '', text, flags=re.IGNORECASE)
        
        # Clean up extra whitespace
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = text.strip()
        
        return text
    
    def _is_off_topic(self, message: str) -> bool:
        """Check if message is not related to transit"""
        off_topic_keywords = [
            "weather", "stock", "recipe", "movie", "song", "joke",
            "poem", "story", "game", "sports", "news", "politics",
            "celebrity", "fashion", "dating", "homework", "code review"
        ]
        message_lower = message.lower()
        
        # Check for off-topic keywords
        for keyword in off_topic_keywords:
            if keyword in message_lower:
                # Double check it's not transit-related
                transit_keywords = ["transit", "bus", "route", "train", "stop", "delay", "schedule"]
                if not any(tk in message_lower for tk in transit_keywords):
                    return True
        
        return False
    
    def _extract_sql(self, text: str) -> Optional[str]:
        """Extract SQL query from LLM response"""
        # Look for SQL in code blocks
        patterns = [
            r'```sql\n(.*?)\n```',
            r'```\n(SELECT.*?)\n```',
            r'`(SELECT[^`]+)`'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        # Look for standalone SELECT statements
        match = re.search(r'(SELECT\s+.+?(?:;|$))', text, re.DOTALL | re.IGNORECASE)
        if match:
            sql = match.group(1).strip()
            if len(sql) > 20:  # Avoid false positives
                return sql
        
        return None
    
    def _extract_sql_from_response(self, text: str) -> Optional[str]:
        """Extract SQL query from LLM response with SQL_QUERY_START/END markers"""
        # Look for SQL_QUERY_START ... SQL_QUERY_END
        pattern = r'SQL_QUERY_START\s*(.*?)\s*SQL_QUERY_END'
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        if match:
            sql = match.group(1).strip()
            # Remove any markdown code blocks
            sql = re.sub(r'```sql\s*', '', sql, flags=re.IGNORECASE)
            sql = re.sub(r'```\s*', '', sql)
            if len(sql) > 20:
                return sql
        
        # Fallback to regular SQL extraction
        return self._extract_sql(text)
    
    def _execute_sql(self, sql: str) -> Dict:
        """Execute SQL query on Snowflake"""
        if not self.snowflake_conn:
            return {"success": False, "data": None, "error": "No database connection"}
        
        try:
            from config.warehouse_config import get_warehouse_config
            config = get_warehouse_config()
            snowflake_config = config.get_snowflake_config()
            database = snowflake_config.get('database', 'USER_DB_HORNET')
            
            # Ensure database is fully qualified in query
            # Replace schema references with fully qualified names
            sql = sql.replace('ANALYTICS.', f'{database}.ANALYTICS.')
            sql = sql.replace('STAGING.', f'{database}.STAGING.')
            sql = sql.replace('ML.', f'{database}.ANALYTICS_ML.')
            
            cursor = self.snowflake_conn.cursor()
            cursor.execute(sql)
            columns = [col[0] for col in cursor.description] if cursor.description else []
            rows = cursor.fetchall()
            cursor.close()
            
            # Convert to list of dicts
            data = [dict(zip(columns, row)) for row in rows] if columns else []
            
            return {"success": True, "data": data}
        except Exception as e:
            print(f"SQL execution error: {e}")
            return {"success": False, "data": None, "error": str(e)}
    
    def _enhance_with_data(
        self, 
        response: str, 
        data: List[Dict],
        original_question: str
    ) -> str:
        """Enhance LLM response with actual query results"""
        if not data:
            return response
        
        # Add actual data summary
        data_summary = "\n\n📊 **Live Data:**\n"
        
        for row in data[:10]:  # Limit to 10 rows
            row_str = " | ".join([f"{k}: {v}" for k, v in row.items()])
            
            # Add severity indicators for performance metrics
            for key, value in row.items():
                if isinstance(value, (int, float)):
                    if 'ON_TIME' in key.upper() or 'RELIABILITY' in key.upper():
                        if value >= 90:
                            row_str = f"🟢 {row_str}"
                        elif value >= 75:
                            row_str = f"🟡 {row_str}"
                        else:
                            row_str = f"🔴 {row_str}"
                        break
            
            data_summary += f"• {row_str}\n"
        
        if len(data) > 10:
            data_summary += f"\n_...and {len(data) - 10} more rows_"
        
        return response + data_summary
    
    def get_quick_stats(self) -> Dict:
        """Get quick stats for display (without LLM)"""
        if not self.snowflake_conn:
            return None
        
        try:
            stats = {}
            cursor = self.snowflake_conn.cursor()
            
            # On-time performance
            cursor.execute("""
                SELECT AVG(ON_TIME_PCT) as avg_otp 
                FROM ANALYTICS.RELIABILITY_METRICS
            """)
            row = cursor.fetchone()
            stats["on_time_pct"] = round(row[0], 1) if row and row[0] else 0
            
            # Total revenue
            cursor.execute("""
                SELECT SUM(ESTIMATED_DAILY_REVENUE) as total_revenue 
                FROM ANALYTICS.REVENUE_METRICS
            """)
            row = cursor.fetchone()
            stats["total_revenue"] = round(row[0], 2) if row and row[0] else 0
            
            # Route count
            cursor.execute("""
                SELECT COUNT(DISTINCT ROUTE_ID) as route_count 
                FROM ANALYTICS.RELIABILITY_METRICS
            """)
            row = cursor.fetchone()
            stats["route_count"] = row[0] if row else 0
            
            cursor.close()
            return stats
            
        except Exception as e:
            return {"error": str(e)}
    
    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []
    
    def _needs_data_query(self, message: str) -> bool:
        """Determine if message needs a data query"""
        query_keywords = [
            "delay", "on-time", "performance", "reliability", "revenue", "utilization",
            "route", "stop", "departure", "arrival", "schedule", "which", "what", "how many",
            "average", "total", "count", "highest", "lowest", "best", "worst", "top", "bottom"
        ]
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in query_keywords)
    
    def _generate_sql_query(self, user_message: str) -> Optional[str]:
        """Generate SQL query based on user question"""
        message_lower = user_message.lower()
        
        # Route delays query
        if "delay" in message_lower and ("route" in message_lower or "highest" in message_lower or "which" in message_lower):
            return """
                SELECT 
                    ROUTE_SHORT_NAME,
                    ROUTE_LONG_NAME,
                    AGENCY,
                    AVG(DELAY_SECONDS) as AVG_DELAY_SEC,
                    COUNT(*) as TOTAL_DEPARTURES,
                    COUNT(CASE WHEN DELAY_SECONDS > 0 THEN 1 END) as DELAYED_COUNT
                FROM USER_DB_HORNET.LANDING.LANDING_STREAMING_DEPARTURES
                WHERE DELAY_SECONDS IS NOT NULL AND DELAY_SECONDS > 0
                GROUP BY ROUTE_SHORT_NAME, ROUTE_LONG_NAME, AGENCY
                ORDER BY AVG_DELAY_SEC DESC
                LIMIT 10
            """
        
        # On-time performance query
        if "on-time" in message_lower or "performance" in message_lower:
            return """
                SELECT 
                    ROUTE_SHORT_NAME,
                    ROUTE_LONG_NAME,
                    AGENCY,
                    COUNT(*) as TOTAL,
                    COUNT(CASE WHEN DELAY_SECONDS <= 0 THEN 1 END) as ON_TIME,
                    (COUNT(CASE WHEN DELAY_SECONDS <= 0 THEN 1 END) * 100.0 / COUNT(*)) as ON_TIME_PCT,
                    AVG(CASE WHEN DELAY_SECONDS > 0 THEN DELAY_SECONDS END) as AVG_DELAY_SEC
                FROM USER_DB_HORNET.LANDING.LANDING_STREAMING_DEPARTURES
                WHERE DELAY_SECONDS IS NOT NULL
                GROUP BY ROUTE_SHORT_NAME, ROUTE_LONG_NAME, AGENCY
                ORDER BY ON_TIME_PCT ASC
            """
        
        # Route performance/reliability
        if "reliability" in message_lower or "performance" in message_lower:
            return """
                SELECT 
                    r.ROUTE_SHORT_NAME,
                    r.ROUTE_LONG_NAME,
                    r.AGENCY,
                    COUNT(DISTINCT st.STOP_ID) as STOPS_SERVED,
                    COUNT(st.STOP_ID) as TOTAL_DEPARTURES
                FROM USER_DB_HORNET.RAW.STG_GTFS_ROUTES r
                INNER JOIN USER_DB_HORNET.RAW.STG_GTFS_TRIPS t ON r.ROUTE_ID = t.ROUTE_ID
                INNER JOIN USER_DB_HORNET.RAW.STG_GTFS_STOP_TIMES st ON t.TRIP_ID = st.TRIP_ID
                GROUP BY r.ROUTE_SHORT_NAME, r.ROUTE_LONG_NAME, r.AGENCY
                ORDER BY TOTAL_DEPARTURES DESC
                LIMIT 20
            """
        
        # Revenue query
        if "revenue" in message_lower:
            return """
                SELECT 
                    r.ROUTE_SHORT_NAME,
                    r.ROUTE_LONG_NAME,
                    r.AGENCY,
                    COUNT(st.STOP_ID) as TOTAL_DEPARTURES,
                    (COUNT(st.STOP_ID) * 20 * 2.50) as ESTIMATED_DAILY_REVENUE
                FROM USER_DB_HORNET.RAW.STG_GTFS_ROUTES r
                INNER JOIN USER_DB_HORNET.RAW.STG_GTFS_TRIPS t ON r.ROUTE_ID = t.ROUTE_ID
                INNER JOIN USER_DB_HORNET.RAW.STG_GTFS_STOP_TIMES st ON t.TRIP_ID = st.TRIP_ID
                GROUP BY r.ROUTE_SHORT_NAME, r.ROUTE_LONG_NAME, r.AGENCY
                ORDER BY ESTIMATED_DAILY_REVENUE DESC
                LIMIT 10
            """
        
        # General route information
        if "route" in message_lower and ("which" in message_lower or "what" in message_lower or "list" in message_lower):
            return """
                SELECT DISTINCT
                    ROUTE_SHORT_NAME,
                    ROUTE_LONG_NAME,
                    AGENCY
                FROM USER_DB_HORNET.RAW.STG_GTFS_ROUTES
                WHERE AGENCY IN ('BART', 'VTA')
                ORDER BY AGENCY, ROUTE_SHORT_NAME
                LIMIT 50
            """
        
        # Default: try to get route delays
        if "delay" in message_lower:
            return """
                SELECT 
                    ROUTE_SHORT_NAME,
                    ROUTE_LONG_NAME,
                    AGENCY,
                    AVG(DELAY_SECONDS) as AVG_DELAY_SEC,
                    COUNT(*) as TOTAL
                FROM USER_DB_HORNET.LANDING.LANDING_STREAMING_DEPARTURES
                WHERE DELAY_SECONDS IS NOT NULL
                GROUP BY ROUTE_SHORT_NAME, ROUTE_LONG_NAME, AGENCY
                ORDER BY AVG_DELAY_SEC DESC
                LIMIT 10
            """
        
        return None
    
    def _generate_response_from_data(self, user_message: str, data: List[Dict]) -> str:
        """Generate human-readable response from query results"""
        if not data:
            return "I checked the transit data, but no information was found for your question."
        
        message_lower = user_message.lower()
        
        # Route delays response
        if "delay" in message_lower and ("route" in message_lower or "highest" in message_lower):
            response = "Here are the routes with the highest delays:\n\n"
            for i, row in enumerate(data[:10], 1):
                route_name = row.get('ROUTE_LONG_NAME') or row.get('ROUTE_SHORT_NAME') or 'Unknown'
                agency = row.get('AGENCY', 'Unknown')
                avg_delay_sec = row.get('AVG_DELAY_SEC', 0) or 0
                avg_delay_min = round(avg_delay_sec / 60, 1)
                total = row.get('TOTAL_DEPARTURES', 0) or row.get('TOTAL', 0) or 0
                
                if avg_delay_min > 10:
                    status = "🔴"
                elif avg_delay_min > 5:
                    status = "🟡"
                else:
                    status = "🟢"
                
                response += f"{status} **{route_name}** ({agency}): {avg_delay_min} min avg delay ({total} departures)\n"
            
            return response
        
        # On-time performance response
        if "on-time" in message_lower or ("performance" in message_lower and "on" in message_lower):
            if len(data) == 0:
                return "No on-time performance data is currently available. This might be because streaming data with delay information hasn't been collected yet."
            
            response = "Here's the on-time performance by route:\n\n"
            shown_count = 0
            for row in data[:10]:
                route_name = row.get('ROUTE_LONG_NAME') or row.get('ROUTE_SHORT_NAME') or row.get('ROUTE_ID', 'Unknown')
                agency = row.get('AGENCY', 'Unknown')
                on_time_pct = row.get('ON_TIME_PCT', 0) or 0
                total = row.get('TOTAL', 0) or 0
                avg_delay_sec = row.get('AVG_DELAY_SEC', 0) or 0
                avg_delay_min = round(avg_delay_sec / 60, 1) if avg_delay_sec else 0
                
                if on_time_pct >= 90:
                    status = "🟢"
                elif on_time_pct >= 75:
                    status = "🟡"
                else:
                    status = "🔴"
                
                response += f"{status} **{route_name}** ({agency}): {on_time_pct:.1f}% on-time"
                if total > 0:
                    response += f" ({total} total departures)"
                if avg_delay_min > 0:
                    response += f", {avg_delay_min} min avg delay"
                response += "\n"
                shown_count += 1
            
            if len(data) > shown_count:
                response += f"\n(Showing {shown_count} of {len(data)} routes)"
            
            return response
        
        # Default response - format based on data structure
        if len(data) == 0:
            return "No data found for your query. Please try asking about a different route, stop, or metric."
        
        response = f"Here's the information from your transit data ({len(data)} result{'s' if len(data) != 1 else ''}):\n\n"
        
        # If data has common transit fields, format nicely
        for i, row in enumerate(data[:10], 1):
            route_name = row.get('ROUTE_LONG_NAME') or row.get('ROUTE_SHORT_NAME') or row.get('ROUTE_ID', 'Unknown')
            agency = row.get('AGENCY', 'Unknown')
            
            if route_name != 'Unknown' or agency != 'Unknown':
                response += f"{i}. **{route_name}** ({agency})"
                # Add other relevant fields
                for key, value in row.items():
                    if key not in ['ROUTE_LONG_NAME', 'ROUTE_SHORT_NAME', 'ROUTE_ID', 'AGENCY'] and value is not None:
                        if isinstance(value, (int, float)):
                            response += f" | {key}: {value}"
                        else:
                            response += f" | {key}: {str(value)[:50]}"
                response += "\n"
            else:
                # Generic format
                items = [f"{k}: {v}" for k, v in row.items() if v is not None][:5]
                response += f"{i}. " + " | ".join(items) + "\n"
        
        if len(data) > 10:
            response += f"\n(Showing 10 of {len(data)} results)"
        
        return response
    
    def _get_llm_response_with_context(self, user_message: str) -> str:
        """Get LLM response with data context"""
        data_context = self._get_current_data_context()
        
        # Enhanced system prompt that emphasizes transit data only
        system_prompt = f"""You are a transit analytics assistant for BART and VTA transit systems.

{SCHEMA_CONTEXT}

## CRITICAL RULES:
1. **NEVER** mention airlines, flights, airports, or any non-transit data
2. **ALWAYS** assume questions are about BART/VTA transit routes, stops, departures, delays
3. If you don't have data, say "No data available" - NEVER make up numbers
4. Use 🟢🟡🔴 for metrics
5. Be concise and direct
"""
        
        messages = [
            {"role": "system", "content": system_prompt}
        ]
        
        # Add current data context
        if data_context:
            messages.append({
                "role": "system", 
                "content": f"CURRENT LIVE DATA:\n{data_context}\n\nUse this data to answer questions. If data is not available, say so - do NOT make up numbers. NEVER mention airlines or flights."
            })
        
        # Add conversation history
        for msg in self.conversation_history[-self.max_history:]:
            messages.append(msg)
        
        # Add current message with explicit transit context
        transit_message = f"{user_message}\n\n[Remember: This is about BART/VTA transit data, NOT airlines or flights]"
        messages.append({"role": "user", "content": transit_message})
        
        # Get LLM response
        result = self.client.chat(messages, max_tokens=800, temperature=0.2)
        
        if not result["success"]:
            return "I'm having trouble connecting to the AI service. Please try again later."
        
        response = result["content"]
        
        # Remove any mentions of airlines/flights if they slip through
        response = response.replace("airline", "transit route")
        response = response.replace("flight", "departure")
        response = response.replace("airport", "transit stop")
        response = response.replace("JFK", "transit stop")
        response = response.replace("Hartsfield-Jackson", "transit stop")
        response = response.replace("Southwest Airlines", "transit route")
        
        return response

