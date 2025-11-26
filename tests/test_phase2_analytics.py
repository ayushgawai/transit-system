#!/usr/bin/env python3
"""
Phase 2 Unit Tests: Analytics Models
=====================================

Tests for:
1. All dbt models run successfully
2. Analytics tables exist and have data
3. Metrics calculations are valid
4. Decision support recommendations are generated

Run with:
    python tests/test_phase2_analytics.py
"""

import os
import sys
from pathlib import Path
from datetime import datetime

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import yaml
import snowflake.connector


class TestResults:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.results = []
    
    def add(self, name: str, status: str, message: str = ""):
        self.results.append({"name": name, "status": status, "message": message})
        if status == "PASS":
            self.passed += 1
        else:
            self.failed += 1
    
    def summary(self) -> str:
        return f"PASS: {self.passed} | FAIL: {self.failed}"


def load_secrets() -> dict:
    with open(project_root / "secrets.yaml", 'r') as f:
        return yaml.safe_load(f)


def get_connection():
    secrets = load_secrets()
    return snowflake.connector.connect(
        account=secrets['SNOWFLAKE_ACCOUNT'],
        user=secrets['SNOWFLAKE_USER'],
        password=secrets['SNOWFLAKE_PASSWORD'],
        warehouse=secrets['SNOWFLAKE_WAREHOUSE'],
        database=secrets['SNOWFLAKE_DATABASE'],
        role=secrets['SNOWFLAKE_ROLE']
    )


# ============================================================================
# TEST SUITE 1: Analytics Tables Exist
# ============================================================================

def test_reliability_metrics_exists(results: TestResults):
    """Test 1.1: reliability_metrics table exists and has data"""
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM STAGING_analytics.reliability_metrics")
        count = cur.fetchone()[0]
        cur.close()
        conn.close()
        
        if count > 0:
            results.add("1.1 reliability_metrics", "PASS", f"{count} rows")
            return True
        else:
            results.add("1.1 reliability_metrics", "FAIL", "No data")
            return False
    except Exception as e:
        results.add("1.1 reliability_metrics", "FAIL", str(e))
        return False


def test_demand_metrics_exists(results: TestResults):
    """Test 1.2: demand_metrics table exists and has data"""
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM STAGING_analytics.demand_metrics")
        count = cur.fetchone()[0]
        cur.close()
        conn.close()
        
        if count > 0:
            results.add("1.2 demand_metrics", "PASS", f"{count} rows")
            return True
        else:
            results.add("1.2 demand_metrics", "FAIL", "No data")
            return False
    except Exception as e:
        results.add("1.2 demand_metrics", "FAIL", str(e))
        return False


def test_crowding_metrics_exists(results: TestResults):
    """Test 1.3: crowding_metrics table exists and has data"""
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM STAGING_analytics.crowding_metrics")
        count = cur.fetchone()[0]
        cur.close()
        conn.close()
        
        if count > 0:
            results.add("1.3 crowding_metrics", "PASS", f"{count} rows")
            return True
        else:
            results.add("1.3 crowding_metrics", "FAIL", "No data")
            return False
    except Exception as e:
        results.add("1.3 crowding_metrics", "FAIL", str(e))
        return False


def test_revenue_metrics_exists(results: TestResults):
    """Test 1.4: revenue_metrics table exists and has data"""
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM STAGING_analytics.revenue_metrics")
        count = cur.fetchone()[0]
        cur.close()
        conn.close()
        
        if count > 0:
            results.add("1.4 revenue_metrics", "PASS", f"{count} rows")
            return True
        else:
            results.add("1.4 revenue_metrics", "FAIL", "No data")
            return False
    except Exception as e:
        results.add("1.4 revenue_metrics", "FAIL", str(e))
        return False


def test_decision_support_exists(results: TestResults):
    """Test 1.5: decision_support table exists and has data"""
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM STAGING_analytics.decision_support")
        count = cur.fetchone()[0]
        cur.close()
        conn.close()
        
        if count > 0:
            results.add("1.5 decision_support", "PASS", f"{count} rows")
            return True
        else:
            results.add("1.5 decision_support", "FAIL", "No data")
            return False
    except Exception as e:
        results.add("1.5 decision_support", "FAIL", str(e))
        return False


# ============================================================================
# TEST SUITE 2: Metrics Validation
# ============================================================================

def test_reliability_score_range(results: TestResults):
    """Test 2.1: reliability_score is between 0 and 100"""
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT 
                MIN(reliability_score) AS min_score,
                MAX(reliability_score) AS max_score,
                COUNT(CASE WHEN reliability_score < 0 OR reliability_score > 100 THEN 1 END) AS invalid_count
            FROM STAGING_analytics.reliability_metrics
            WHERE reliability_score IS NOT NULL
        """)
        row = cur.fetchone()
        min_score, max_score, invalid_count = row
        cur.close()
        conn.close()
        
        if invalid_count == 0 and min_score >= 0 and max_score <= 100:
            results.add("2.1 Reliability Score Range", "PASS", f"Range: {min_score:.1f} - {max_score:.1f}")
            return True
        else:
            results.add("2.1 Reliability Score Range", "FAIL", f"Invalid count: {invalid_count}")
            return False
    except Exception as e:
        results.add("2.1 Reliability Score Range", "FAIL", str(e))
        return False


def test_on_time_pct_range(results: TestResults):
    """Test 2.2: on_time_pct is between 0 and 100"""
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT 
                MIN(on_time_pct) AS min_pct,
                MAX(on_time_pct) AS max_pct
            FROM STAGING_analytics.reliability_metrics
            WHERE on_time_pct IS NOT NULL
        """)
        row = cur.fetchone()
        min_pct, max_pct = row
        cur.close()
        conn.close()
        
        if min_pct >= 0 and max_pct <= 100:
            results.add("2.2 On-Time Pct Range", "PASS", f"Range: {min_pct:.1f}% - {max_pct:.1f}%")
            return True
        else:
            results.add("2.2 On-Time Pct Range", "FAIL", f"Out of range: {min_pct} - {max_pct}")
            return False
    except Exception as e:
        results.add("2.2 On-Time Pct Range", "FAIL", str(e))
        return False


def test_demand_intensity_range(results: TestResults):
    """Test 2.3: demand_intensity_score is between 0 and 100"""
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT 
                MIN(demand_intensity_score) AS min_score,
                MAX(demand_intensity_score) AS max_score
            FROM STAGING_analytics.demand_metrics
        """)
        row = cur.fetchone()
        min_score, max_score = row
        cur.close()
        conn.close()
        
        if min_score >= 0 and max_score <= 100:
            results.add("2.3 Demand Intensity Range", "PASS", f"Range: {min_score} - {max_score}")
            return True
        else:
            results.add("2.3 Demand Intensity Range", "FAIL", f"Out of range: {min_score} - {max_score}")
            return False
    except Exception as e:
        results.add("2.3 Demand Intensity Range", "FAIL", str(e))
        return False


def test_revenue_positive(results: TestResults):
    """Test 2.4: estimated_revenue is non-negative"""
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT 
                COUNT(CASE WHEN estimated_revenue < 0 THEN 1 END) AS negative_count,
                SUM(estimated_revenue) AS total_revenue
            FROM STAGING_analytics.revenue_metrics
        """)
        row = cur.fetchone()
        negative_count, total_revenue = row
        cur.close()
        conn.close()
        
        if negative_count == 0:
            results.add("2.4 Revenue Non-Negative", "PASS", f"Total: ${total_revenue:,.2f}")
            return True
        else:
            results.add("2.4 Revenue Non-Negative", "FAIL", f"{negative_count} negative values")
            return False
    except Exception as e:
        results.add("2.4 Revenue Non-Negative", "FAIL", str(e))
        return False


# ============================================================================
# TEST SUITE 3: Decision Support Quality
# ============================================================================

def test_recommendations_have_types(results: TestResults):
    """Test 3.1: All recommendations have a valid type"""
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT DISTINCT recommendation_type 
            FROM STAGING_analytics.decision_support
        """)
        types = [row[0] for row in cur.fetchall()]
        cur.close()
        conn.close()
        
        valid_types = {'ADD_BUSES', 'IMPROVE_RELIABILITY', 'REDUCE_FREQUENCY', 
                       'FLEET_REALLOCATION', 'REVENUE_RECOVERY', 'INCREASE_FREQUENCY', 'MONITOR'}
        invalid = [t for t in types if t not in valid_types]
        
        if not invalid:
            results.add("3.1 Recommendation Types", "PASS", f"Found: {types}")
            return True
        else:
            results.add("3.1 Recommendation Types", "FAIL", f"Invalid types: {invalid}")
            return False
    except Exception as e:
        results.add("3.1 Recommendation Types", "FAIL", str(e))
        return False


def test_priority_scores_valid(results: TestResults):
    """Test 3.2: Priority scores are between 0 and 100"""
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT 
                MIN(priority_score) AS min_score,
                MAX(priority_score) AS max_score
            FROM STAGING_analytics.decision_support
        """)
        row = cur.fetchone()
        min_score, max_score = row
        cur.close()
        conn.close()
        
        if min_score >= 0 and max_score <= 100:
            results.add("3.2 Priority Score Range", "PASS", f"Range: {min_score} - {max_score}")
            return True
        else:
            results.add("3.2 Priority Score Range", "FAIL", f"Out of range: {min_score} - {max_score}")
            return False
    except Exception as e:
        results.add("3.2 Priority Score Range", "FAIL", str(e))
        return False


def test_recommendations_have_descriptions(results: TestResults):
    """Test 3.3: All recommendations have descriptions"""
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT 
                COUNT(*) AS total,
                COUNT(recommendation_description) AS has_desc
            FROM STAGING_analytics.decision_support
        """)
        row = cur.fetchone()
        total, has_desc = row
        cur.close()
        conn.close()
        
        if total == has_desc:
            results.add("3.3 Recommendation Descriptions", "PASS", f"All {total} have descriptions")
            return True
        else:
            results.add("3.3 Recommendation Descriptions", "FAIL", f"{total - has_desc} missing descriptions")
            return False
    except Exception as e:
        results.add("3.3 Recommendation Descriptions", "FAIL", str(e))
        return False


# ============================================================================
# TEST SUITE 4: Sample Data Verification
# ============================================================================

def test_sample_reliability_data(results: TestResults):
    """Test 4.1: Sample reliability data looks reasonable"""
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT 
                route_global_id,
                route_short_name,
                on_time_pct,
                reliability_score,
                total_departures
            FROM STAGING_analytics.reliability_metrics
            LIMIT 3
        """)
        rows = cur.fetchall()
        cur.close()
        conn.close()
        
        if rows:
            sample = rows[0]
            results.add("4.1 Sample Reliability", "PASS", 
                       f"Route {sample[1]}: {sample[2]:.1f}% on-time, score={sample[3]:.1f}")
            return True
        else:
            results.add("4.1 Sample Reliability", "FAIL", "No data")
            return False
    except Exception as e:
        results.add("4.1 Sample Reliability", "FAIL", str(e))
        return False


def test_sample_decision_support(results: TestResults):
    """Test 4.2: Sample decision support recommendations"""
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT 
                route_short_name,
                recommendation_type,
                priority_score,
                recommendation_description
            FROM STAGING_analytics.decision_support
            ORDER BY priority_score DESC
            LIMIT 1
        """)
        row = cur.fetchone()
        cur.close()
        conn.close()
        
        if row:
            results.add("4.2 Sample Recommendation", "PASS", 
                       f"Route {row[0]}: {row[1]} (priority={row[2]})")
            return True
        else:
            results.add("4.2 Sample Recommendation", "FAIL", "No recommendations")
            return False
    except Exception as e:
        results.add("4.2 Sample Recommendation", "FAIL", str(e))
        return False


# ============================================================================
# MAIN TEST RUNNER
# ============================================================================

def run_all_tests():
    print("=" * 70)
    print("PHASE 2 UNIT TESTS: Analytics Models")
    print("=" * 70)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    results = TestResults()
    
    # Suite 1: Tables Exist
    print("📊 Suite 1: Analytics Tables Exist")
    print("-" * 40)
    test_reliability_metrics_exists(results)
    test_demand_metrics_exists(results)
    test_crowding_metrics_exists(results)
    test_revenue_metrics_exists(results)
    test_decision_support_exists(results)
    print()
    
    # Suite 2: Metrics Validation
    print("✅ Suite 2: Metrics Validation")
    print("-" * 40)
    test_reliability_score_range(results)
    test_on_time_pct_range(results)
    test_demand_intensity_range(results)
    test_revenue_positive(results)
    print()
    
    # Suite 3: Decision Support
    print("🤖 Suite 3: Decision Support Quality")
    print("-" * 40)
    test_recommendations_have_types(results)
    test_priority_scores_valid(results)
    test_recommendations_have_descriptions(results)
    print()
    
    # Suite 4: Sample Data
    print("📋 Suite 4: Sample Data Verification")
    print("-" * 40)
    test_sample_reliability_data(results)
    test_sample_decision_support(results)
    print()
    
    # Print Results
    print("=" * 70)
    print("TEST RESULTS")
    print("=" * 70)
    
    for r in results.results:
        icon = "✅" if r["status"] == "PASS" else "❌"
        print(f"  {icon} {r['name']}: {r['status']}")
        if r["message"]:
            print(f"      └─ {r['message']}")
    
    print()
    print("-" * 70)
    print(f"SUMMARY: {results.summary()}")
    print("-" * 70)
    
    if results.failed == 0:
        print("\n🎉 ALL TESTS PASSED! Phase 2 is complete.")
        print("   Ready to proceed to Phase 3: Admin UI")
        return 0
    else:
        print(f"\n⚠️  {results.failed} test(s) failed.")
        return 1


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)

