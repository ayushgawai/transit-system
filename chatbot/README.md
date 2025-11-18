# Transit Analytics Chatbot

Natural language query interface for the Transit Service Reliability & Demand Planning System.

## Features

- Answer questions about transit service reliability, demand, crowding, revenue
- Query ML forecasts and predictions
- Get decision support recommendations
- Translate natural language to Snowflake SQL queries
- Format results in clear, concise answers

## Setup

### Option 1: OpenAI (Recommended - Free Tier)

1. Get OpenAI API key: https://platform.openai.com/api-keys
2. Set environment variable:
   ```bash
   export OPENAI_API_KEY="your-api-key"
   ```

3. Run chatbot:
   ```bash
   cd chatbot
   pip install flask openai snowflake-connector-python
   python chatbot_api.py
   ```

### Option 2: Local LLM (Ollama/Llama)

1. Install Ollama: https://ollama.ai
2. Download Llama model:
   ```bash
   ollama pull llama2
   ```

3. Update `chatbot_api.py` to use Ollama API instead of OpenAI

## API Endpoints

### POST /query

Process natural language query.

**Request**:
```json
{
  "question": "Which route tomorrow at 8am is likely to be most crowded?",
  "include_sql": false
}
```

**Response**:
```json
{
  "question": "Which route tomorrow at 8am is likely to be most crowded?",
  "answer": "Based on ML forecasts for tomorrow at 8am, Route 1 (Blue Line) is predicted to be the most crowded...",
  "result_count": 5,
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### POST /query/sql

Execute SQL query directly (for testing).

**Request**:
```json
{
  "sql": "SELECT * FROM MARTS.RELIABILITY_METRICS LIMIT 10"
}
```

### GET /health

Health check endpoint.

## Example Questions

- "Which route tomorrow at 8am is likely to be most crowded?"
- "What's the on-time performance for Route 1 this week?"
- "Which stops have the highest boarding rates?"
- "Show me revenue impact of delays on Route 5"
- "Recommend fleet reallocation for tomorrow's morning rush"
- "What routes need frequency increases?"
- "Which routes have the highest revenue loss due to delays?"

## Deployment

### Lambda Function

```bash
zip -r chatbot.zip chatbot_api.py
aws lambda create-function \
  --function-name transit-chatbot \
  --runtime python3.9 \
  --role <lambda-execution-role-arn> \
  --handler chatbot_api.handler \
  --zip-file fileb://chatbot.zip \
  --environment Variables={OPENAI_API_KEY=<key>,SNOWFLAKE_ACCOUNT=<account>}
```

### API Gateway

Create API Gateway REST API and connect to Lambda function for HTTP access.

### Docker

```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY chatbot/ .
RUN pip install flask openai snowflake-connector-python
EXPOSE 5000
CMD ["python", "chatbot_api.py"]
```

## Cost Considerations

- **OpenAI GPT-3.5-turbo**: ~$0.002 per 1K tokens (free tier: $5 credit)
- **Snowflake queries**: Minimal cost if using free tier (warehouse auto-suspend)
- **Lambda**: Free tier: 1M requests/month
- **API Gateway**: Free tier: 1M requests/month

For production, consider caching common queries and using local LLM for cost savings.

