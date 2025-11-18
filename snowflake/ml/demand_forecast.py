"""
Snowflake ML Model: Demand Forecasting

This script trains and generates demand forecasts using Snowflake ML (Snowpark).
Forecasts boarding demand by route/stop/hour for next 24-48 hours.
"""

import snowflake.connector
from snowflake.snowpark import Session
from snowflake.snowpark.functions import col
import pandas as pd
from typing import Dict, Any
import os

# Snowflake connection parameters (from config or environment)
def get_snowflake_session() -> Session:
    """Create Snowflake session from environment variables."""
    connection_parameters = {
        "account": os.environ.get("SNOWFLAKE_ACCOUNT"),
        "user": os.environ.get("SNOWFLAKE_USER"),
        "password": os.environ.get("SNOWFLAKE_PASSWORD"),
        "warehouse": "TRANSIT_WH",
        "database": "TRANSIT_DB",
        "schema": "ML",
        "role": "TRANSIT_ROLE"
    }
    return Session.builder.configs(connection_parameters).create()


def train_demand_forecast_model(session: Session) -> Dict[str, Any]:
    """
    Train demand forecasting model.
    
    Uses historical demand metrics to predict future boarding demand.
    Features: hour_of_day, day_of_week, route_id, stop_id, historical_boarding_avg
    """
    
    # Load historical demand data
    training_data = session.table("MARTS.DEMAND_METRICS").select(
        col("route_id"),
        col("stop_id"),
        col("departure_date"),
        col("departure_day_of_week"),
        col("departure_hour").alias("hour_of_day"),
        col("total_departures").alias("boarding_count"),  # Proxy for actual boardings
        col("morning_peak_departures"),
        col("evening_peak_departures")
    ).filter(
        col("departure_date") >= "CURRENT_DATE - 60"  # Last 60 days
    )
    
    # Calculate historical averages by hour/day_of_week/route
    historical_avg = training_data.group_by(
        col("route_id"),
        col("stop_id"),
        col("hour_of_day"),
        col("departure_day_of_week")
    ).agg(
        {"boarding_count": "avg"}
    ).with_column_renamed("AVG(BOARDING_COUNT)", "historical_avg_boarding")
    
    # Join with training data
    features_df = training_data.join(
        historical_avg,
        on=["route_id", "stop_id", "hour_of_day", "departure_day_of_week"]
    )
    
    # Convert to pandas for modeling (or use Snowpark ML if available)
    training_pd = features_df.to_pandas()
    
    # Simple forecasting model: Time series with seasonality
    # In production, use more sophisticated models (Prophet, ARIMA, LSTM, etc.)
    from sklearn.ensemble import RandomForestRegressor
    import numpy as np
    
    # Prepare features
    X = training_pd[[
        "hour_of_day",
        "departure_day_of_week",
        "historical_avg_boarding"
    ]].fillna(0)
    
    y = training_pd["boarding_count"].fillna(0)
    
    # Train model
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X, y)
    
    # Save model (in production, use Snowflake ML model registry or external storage)
    # For now, return model metrics
    predictions = model.predict(X)
    mae = np.mean(np.abs(predictions - y))
    rmse = np.sqrt(np.mean((predictions - y) ** 2))
    
    return {
        "model_type": "RandomForestRegressor",
        "mae": float(mae),
        "rmse": float(rmse),
        "training_samples": len(training_pd),
        "model_params": model.get_params()
    }


def generate_demand_forecasts(session: Session, forecast_horizon_hours: int = 24) -> pd.DataFrame:
    """
    Generate demand forecasts for next N hours.
    
    Args:
        session: Snowflake session
        forecast_horizon_hours: Number of hours ahead to forecast
        
    Returns:
        DataFrame with forecasts
    """
    
    from datetime import datetime, timedelta
    
    # Get base features (hour, day_of_week) for forecast period
    forecast_start = datetime.now()
    forecast_dates = []
    for hour in range(forecast_horizon_hours):
        forecast_time = forecast_start + timedelta(hours=hour)
        forecast_dates.append({
            "hour_of_day": forecast_time.hour,
            "departure_day_of_week": forecast_time.weekday() + 1,  # 1=Monday
            "forecast_timestamp": forecast_time
        })
    
    forecast_base = pd.DataFrame(forecast_dates)
    
    # Get historical averages by route/stop/hour/day_of_week
    historical_avg = session.sql("""
        SELECT 
            route_id,
            stop_id,
            EXTRACT(HOUR FROM TO_TIMESTAMP(CONCAT(departure_date, ' ', departure_hour, ':00:00'))) AS hour_of_day,
            departure_day_of_week,
            AVG(total_departures) AS historical_avg_boarding
        FROM MARTS.DEMAND_METRICS
        WHERE departure_date >= CURRENT_DATE - 30
        GROUP BY route_id, stop_id, hour_of_day, departure_day_of_week
    """).to_pandas()
    
    # Cross join forecast base with all route/stop combinations
    routes_stops = session.sql("""
        SELECT DISTINCT route_id, stop_id
        FROM MARTS.DEMAND_METRICS
    """).to_pandas()
    
    # Create forecast input features
    forecast_input = forecast_base.merge(
        routes_stops,
        how='cross'
    ).merge(
        historical_avg,
        on=["route_id", "stop_id", "hour_of_day", "departure_day_of_week"],
        how='left'
    ).fillna(0)
    
    # Generate forecasts using trained model
    # In production, load saved model and predict
    # For now, use simple average-based forecast
    forecasts = forecast_input.copy()
    forecasts["predicted_boarding"] = forecasts["historical_avg_boarding"]
    
    return forecasts[[
        "route_id",
        "stop_id",
        "forecast_timestamp",
        "predicted_boarding"
    ]]


def save_forecasts_to_snowflake(session: Session, forecasts: pd.DataFrame):
    """Save forecasts to Snowflake ML.FORECASTS table."""
    
    # Create Snowpark DataFrame from pandas
    forecasts_sp = session.create_dataframe(forecasts)
    
    # Add metadata
    forecasts_sp = forecasts_sp.with_column(
        "id",
        col("route_id") + "_" + col("stop_id") + "_" + col("forecast_timestamp").cast("STRING")
    ).with_column(
        "forecast_type",
        "demand"
    ).with_column(
        "predicted_value",
        col("predicted_boarding")
    ).with_column(
        "model_version",
        "1.0.0"
    ).select(
        col("id"),
        col("forecast_type"),
        col("route_id"),
        col("stop_id"),
        col("forecast_timestamp").alias("forecast_timestamp"),
        col("predicted_value"),
        col("confidence_interval_lower"),  # Would be calculated by model
        col("confidence_interval_upper"),  # Would be calculated by model
        col("model_version")
    )
    
    # Write to Snowflake
    forecasts_sp.write.mode("overwrite").save_as_table("ML.FORECASTS")


if __name__ == "__main__":
    # Train model
    session = get_snowflake_session()
    model_metrics = train_demand_forecast_model(session)
    print(f"Model training completed: {model_metrics}")
    
    # Generate forecasts
    forecasts = generate_demand_forecasts(session, forecast_horizon_hours=24)
    print(f"Generated {len(forecasts)} forecasts")
    
    # Save to Snowflake
    save_forecasts_to_snowflake(session, forecasts)
    print("Forecasts saved to Snowflake")

