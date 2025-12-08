"""
Chat Handler
Main logic for processing user questions and generating responses
"""

import re
import json
from typing import Dict, Optional, List, Any
from .perplexity_client import PerplexityClient
from .schema_context import get_system_prompt

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
        
        # First, fetch current data to provide context to LLM
        data_context = self._get_current_data_context()
        
        # Build messages with system prompt, data context, and history
        messages = [
            {"role": "system", "content": get_system_prompt()}
        ]
        
        # Add current data context
        if data_context:
            messages.append({
                "role": "system", 
                "content": f"CURRENT LIVE DATA (use this to answer questions directly):\n{data_context}"
            })
        
        # Add conversation history
        for msg in self.conversation_history[-self.max_history:]:
            messages.append(msg)
        
        # Add current message
        messages.append({"role": "user", "content": user_message})
        
        # Get LLM response
        result = self.client.chat(messages, max_tokens=600, temperature=0.2)
        
        if not result["success"]:
            return {
                "success": False,
                "response": "I'm having trouble connecting to the AI service. Please check with the developer (Ayush Gawai) or try again later.",
                "data": None,
                "error": result.get("error")
            }
        
        response_text = result["content"]
        
        # Clean up any SQL that might have slipped through
        response_text = self._remove_sql_from_response(response_text)
        
        # Update conversation history
        self.conversation_history.append({"role": "user", "content": user_message})
        self.conversation_history.append({"role": "assistant", "content": response_text})
        
        return {
            "success": True,
            "response": response_text,
            "data": None,
            "sql": None  # Don't expose SQL to frontend
        }
    
    def _get_current_data_context(self) -> Optional[str]:
        """Fetch current metrics to provide as context to LLM"""
        if not self.snowflake_conn:
            return None
        
        try:
            cursor = self.snowflake_conn.cursor()
            context_parts = []
            
            # Get reliability metrics by route
            cursor.execute("""
                SELECT ROUTE_ID, ON_TIME_PCT, RELIABILITY_SCORE, AVG_DELAY_MINUTES
                FROM ANALYTICS.RELIABILITY_METRICS
                ORDER BY ROUTE_ID
            """)
            rows = cursor.fetchall()
            if rows:
                context_parts.append("RELIABILITY BY ROUTE:")
                for row in rows:
                    route, otp, rel, delay = row
                    severity = "🟢" if otp >= 90 else "🟡" if otp >= 75 else "🔴"
                    context_parts.append(f"  {severity} {route}: OTP={otp}%, Reliability={rel}, AvgDelay={delay}min")
            
            # Get revenue metrics
            cursor.execute("""
                SELECT ROUTE_ID, ESTIMATED_DAILY_REVENUE, REVENUE_OPPORTUNITY
                FROM ANALYTICS.REVENUE_METRICS
                ORDER BY ROUTE_ID
            """)
            rows = cursor.fetchall()
            if rows:
                context_parts.append("\nREVENUE BY ROUTE:")
                total_rev = 0
                for row in rows:
                    route, rev, opp = row
                    total_rev += float(rev) if rev else 0
                    context_parts.append(f"  {route}: ${rev}/day, Opportunity=${opp}")
                context_parts.append(f"  TOTAL DAILY REVENUE: ${total_rev:.2f}")
            
            # Get crowding/demand info
            cursor.execute("""
                SELECT ROUTE_ID, AVG_OCCUPANCY_RATIO, PEAK_OCCUPANCY_RATIO
                FROM ANALYTICS.CROWDING_METRICS
                ORDER BY ROUTE_ID
            """)
            rows = cursor.fetchall()
            if rows:
                context_parts.append("\nCROWDING BY ROUTE:")
                for row in rows:
                    route, avg_occ, peak_occ = row
                    context_parts.append(f"  {route}: AvgOccupancy={avg_occ}, PeakOccupancy={peak_occ}")
            
            # Get recommendations
            cursor.execute("""
                SELECT ROUTE_ID, RECOMMENDATION_TYPE, RECOMMENDATION_DESCRIPTION, PRIORITY_SCORE
                FROM ANALYTICS.DECISION_SUPPORT
                ORDER BY PRIORITY_SCORE DESC
                LIMIT 5
            """)
            rows = cursor.fetchall()
            if rows:
                context_parts.append("\nTOP RECOMMENDATIONS:")
                for row in rows:
                    route, rec_type, desc, priority = row
                    context_parts.append(f"  Priority {priority}: {route} - {rec_type}: {desc}")
            
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
    
    def _execute_sql(self, sql: str) -> Dict:
        """Execute SQL query on Snowflake"""
        if not self.snowflake_conn:
            return {"success": False, "data": None, "error": "No database connection"}
        
        try:
            cursor = self.snowflake_conn.cursor()
            cursor.execute(sql)
            columns = [col[0] for col in cursor.description]
            rows = cursor.fetchall()
            cursor.close()
            
            # Convert to list of dicts
            data = [dict(zip(columns, row)) for row in rows]
            
            return {"success": True, "data": data}
        except Exception as e:
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

