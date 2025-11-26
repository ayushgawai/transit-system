# ⛔ STOP AWS RESOURCES AFTER TESTING

## CRITICAL: Always Stop Resources After Testing

**Run these commands IMMEDIATELY after testing to avoid charges:**

```bash
# Load secrets first
source scripts/load_secrets.sh

# Delete CloudFormation stack (stops ALL resources)
aws cloudformation delete-stack \
  --stack-name transit-system-dev \
  --profile transit-system

# Wait for deletion (takes 2-5 minutes)
aws cloudformation wait stack-delete-complete \
  --stack-name transit-system-dev \
  --profile transit-system

# Verify deletion
aws cloudformation describe-stacks \
  --stack-name transit-system-dev \
  --profile transit-system 2>&1 | grep -q "does not exist" && echo "✅ Stack deleted" || echo "⚠️ Stack still exists"
```

## Manual Cleanup Checklist

After deleting CloudFormation stack, verify:

- [ ] CloudFormation stack deleted
- [ ] S3 buckets deleted (check AWS Console)
- [ ] Lambda functions deleted
- [ ] EventBridge rules disabled
- [ ] SQS queues deleted
- [ ] IAM roles deleted (if not auto-deleted)
- [ ] CloudWatch alarms deleted
- [ ] SNS topics deleted
- [ ] Secrets Manager secrets deleted (optional - keep if reusing)

## Snowflake Cleanup

```sql
-- Suspend warehouse to stop credit usage
ALTER WAREHOUSE TRANSIT_WH SUSPEND;

-- Check credit usage
SELECT 
    DATE_TRUNC('day', START_TIME) as date,
    SUM(CREDITS_USED) as credits_used
FROM SNOWFLAKE.ACCOUNT_USAGE.WAREHOUSE_METERING_HISTORY
WHERE START_TIME >= CURRENT_DATE - 7
GROUP BY DATE_TRUNC('day', START_TIME)
ORDER BY date DESC;
```

## Cost Check

```bash
# Check AWS costs
aws ce get-cost-and-usage \
  --time-period Start=$(date -u +"%Y-%m-01"),End=$(date -u +"%Y-%m-%d") \
  --granularity MONTHLY \
  --metrics BlendedCost \
  --profile transit-system
```

**REMEMBER: Always stop resources after testing!**

