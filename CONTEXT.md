# 🚌 Transit Service Reliability & Demand Planning System
## Project Context Document

> **Last Updated**: November 26, 2025  
> **Project Type**: MSDA Capstone Project  
> **Status**: Phase 4 Complete - LLM Integration Working  

---

## 📋 Table of Contents

1. [Executive Summary](#executive-summary)
2. [Problem Statement](#problem-statement)
3. [Solution Overview](#solution-overview)
4. [Target Users & Stakeholders](#target-users--stakeholders)
5. [Key Features & Capabilities](#key-features--capabilities)
6. [Technical Architecture](#technical-architecture)
7. [Data Flow & Pipeline](#data-flow--pipeline)
8. [Required Technology Stack](#required-technology-stack)
9. [Current Project Status](#current-project-status)
10. [Project Structure](#project-structure)
11. [Deliverables & Milestones](#deliverables--milestones)
12. [KPIs & Success Metrics](#kpis--success-metrics)
13. [Future Enhancements](#future-enhancements)
14. [Quick Reference](#quick-reference)

---

## Executive Summary

This project builds a **production-ready transit analytics platform** for a metropolitan transit operator. The system transforms raw real-time transit data into actionable intelligence — enabling operations teams to make data-driven decisions about fleet allocation, service reliability, and passenger experience.

### One-Liner
> "We turn live arrivals into explainable reliability KPIs so ops can see and fix headway gaps quickly, optimize fleet usage, and improve service for riders."

### What This Is
- A **full-stack analytics platform** for transit operations teams
- An **internal admin application** with dashboards, AI chatbot, and decision support
- A **streaming data pipeline** processing real-time transit feeds
- A **predictive analytics system** for demand, delays, and crowding forecasting

### What This Is NOT
- A public-facing rider app (this is for internal ops/analytics teams)
- A simple dashboard (this includes AI-powered insights and predictions)
- A static reporting tool (this is near real-time with live data)

---

## Problem Statement

### The Core Problem
Real-time arrival feeds exist, but transit teams don't get **explainable reliability KPIs** (headway health, on-time performance) by route/direction/time window. Decisions are made from raw predictions rather than trustworthy, actionable metrics.

### Specific Pain Points

| Pain Point | Impact |
|------------|--------|
| **No unified view of service health** | Ops can't quickly identify problem areas |
| **Gaps go undetected** | Riders wait too long, trust erodes |
| **Inefficient fleet allocation** | Some routes overcrowded, others run empty |
| **Reactive, not proactive** | Issues discovered after rider complaints |
| **No data-driven staffing** | Dispatch decisions based on gut feel |
| **Revenue leakage** | Poor reliability → fewer riders → less revenue |
| **No predictive capability** | Can't anticipate tomorrow's problems |

### Why Now?
- Transit APIs now provide real-time data that was previously unavailable
- Cloud infrastructure makes streaming analytics affordable
- ML/AI enables predictive insights that weren't possible before
- Post-pandemic transit recovery requires data-driven optimization

---

## Solution Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           DATA SOURCES                                       │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐          │
│  │ TransitApp API   │  │ GTFS Static      │  │ Historical Data  │          │
│  │ (Real-time)      │  │ (Schedules)      │  │ (Archived)       │          │
│  └────────┬─────────┘  └────────┬─────────┘  └────────┬─────────┘          │
└───────────┼─────────────────────┼─────────────────────┼─────────────────────┘
            │                     │                     │
            ▼                     ▼                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                       INGESTION LAYER (AWS)                                  │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐ │
│  │ EventBridge  │──▶│ SQS Queue    │──▶│ Lambda       │──▶│ S3 Raw       │ │
│  │ (Scheduler)  │   │ (Buffer)     │   │ (Ingestion)  │   │ (Data Lake)  │ │
│  └──────────────┘   └──────────────┘   └──────────────┘   └──────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
                                          │
                                          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                       DATA WAREHOUSE (Snowflake)                             │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐ │
│  │ Snowpipe     │──▶│ RAW Schema   │──▶│ STAGING      │──▶│ ANALYTICS    │ │
│  │ (Auto-load)  │   │ (Landing)    │   │ (dbt)        │   │ (Marts)      │ │
│  └──────────────┘   └──────────────┘   └──────────────┘   └──────────────┘ │
│                                                                ┌──────────┐ │
│                                                                │ ML Models│ │
│                                                                └──────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
                                          │
                    ┌─────────────────────┼─────────────────────┐
                    ▼                     ▼                     ▼
┌──────────────────────┐  ┌──────────────────────┐  ┌──────────────────────┐
│   ADMIN UI (Web)     │  │   BI DASHBOARDS      │  │   AI CHATBOT         │
│   - Live Charts      │  │   - Snowsight        │  │   - Natural Language │
│   - AI Suggestions   │  │   - QuickSight       │  │   - SQL Generation   │
│   - Data Explorer    │  │   - Custom Viz       │  │   - Insights         │
│   - API Docs         │  │                      │  │                      │
└──────────────────────┘  └──────────────────────┘  └──────────────────────┘
```

### What We Deliver

1. **Real-Time Data Pipeline**: Continuous ingestion from TransitApp API and GTFS feeds
2. **Data Warehouse**: Clean, modeled data in Snowflake with dimensional design
3. **Analytics Marts**: Pre-computed metrics for reliability, demand, crowding, revenue
4. **ML Predictions**: Demand forecasts, delay predictions, crowding estimates
5. **Interactive Dashboards**: Live visualizations with drill-down capabilities
6. **AI Chatbot**: Natural language interface to query data and get insights
7. **Decision Support**: AI-powered recommendations for fleet optimization
8. **Admin Web UI**: Unified interface for all platform capabilities

---

## Target Users & Stakeholders

### Primary Users

| User Role | Needs | How We Help |
|-----------|-------|-------------|
| **Operations Manager** | Real-time service visibility | Live dashboards, alerts, gap detection |
| **Dispatch Supervisor** | Fleet allocation decisions | AI recommendations, demand forecasts |
| **Analytics Team** | Historical trends, KPIs | Dimensional data model, SQL access |
| **Executive Leadership** | High-level service health | Summary dashboards, revenue impact |
| **Planning Team** | Schedule optimization | Headway analysis, demand patterns |

### Secondary Stakeholders

- **IT/Engineering**: Need clean APIs, good documentation
- **Finance**: Need revenue impact analysis
- **Customer Service**: Need context for rider complaints
- **Marketing/Comms**: Need reliability stats for messaging

---

## Key Features & Capabilities

### 1. 📊 Service Reliability Dashboard

**What It Shows:**
- On-time performance by route/direction/hour
- Headway gaps (actual vs. scheduled)
- Service consistency metrics
- Alert frequency and duration
- Historical trends and comparisons

**Key Metrics:**
- % On-Time Departures
- Average Headway Gap
- Gap Detection Rate (>10 min gaps)
- Service Consistency Score
- p95 Delay Minutes

### 2. 📈 Demand & Crowding Analysis

**What It Shows:**
- Boarding heatmaps by stop/time
- Route popularity rankings
- Peak vs. off-peak patterns
- Capacity utilization estimates
- Crowding forecasts

**Key Questions Answered:**
- Which stops are busiest at what times?
- Which routes are overcrowded vs. underutilized?
- Where do we need more capacity?
- How does demand change by day of week?

### 3. 🤖 AI-Powered Suggestions

**Fleet Optimization Recommendations:**
```
┌─────────────────────────────────────────────────────────────────┐
│  AI RECOMMENDATION                                               │
├─────────────────────────────────────────────────────────────────┤
│  🚌 Route 14 - Mission                                          │
│  ├── Current: 8 buses assigned (AM Peak)                        │
│  ├── Demand: 120% capacity utilization                          │
│  ├── Suggestion: Add 2 buses (8:00-9:30 AM)                     │
│  └── Impact: Reduce crowding by 25%, improve OTP by 8%          │
├─────────────────────────────────────────────────────────────────┤
│  🚌 Route 38 - Geary                                            │
│  ├── Current: 12 buses assigned (Midday)                        │
│  ├── Demand: 45% capacity utilization                           │
│  ├── Suggestion: Reduce to 8 buses (11:00 AM - 2:00 PM)         │
│  └── Impact: Save $X/day, reallocate to Route 14                │
└─────────────────────────────────────────────────────────────────┘
```

**What AI Tells You:**
- Which routes need more/fewer buses and when
- Which time windows have gaps consistently
- Where reliability is hurting ridership
- How to optimize for cost vs. service quality
- Predicted impact of changes

### 4. 💬 AI Chatbot (Natural Language Interface)

**Example Queries:**
- "Which route tomorrow at 8am is likely to be most crowded?"
- "What's the on-time performance for Route 14 this week?"
- "Which stops have the highest boarding rates?"
- "Recommend fleet reallocation for tomorrow's morning rush"
- "Show me the top 5 routes with the worst headway gaps"
- "Compare Monday vs. Friday demand patterns"
- "What's the revenue impact of delays on Route 5?"

**How It Works:**
1. User asks natural language question
2. LLM interprets intent and context
3. System generates appropriate SQL query
4. Query executes against Snowflake
5. Results formatted and explained in plain English
6. Visualizations generated where appropriate

### 5. 💰 Revenue & Efficiency Analysis

**What It Shows:**
- Revenue by route (ridership-based proxy)
- Cost per passenger by route
- Reliability impact on ridership
- Inefficiency identification (empty buses, overcrowding)
- ROI of service improvements

**Key Questions Answered:**
- Which routes are most/least cost-efficient?
- How does poor reliability affect ridership?
- Where can we cut costs without hurting service?
- What's the business case for adding a bus to Route X?

### 6. 🔮 Predictive Analytics

**Forecasts We Provide:**
- **Demand Forecast**: Predicted boardings by stop/route/hour (next 24-48h)
- **Delay Forecast**: Expected delays and their likely causes
- **Crowding Forecast**: Capacity utilization predictions
- **Anomaly Detection**: Early warning for unusual patterns

**Model Features:**
- Hour of day, day of week, seasonality
- Historical patterns by route/stop
- Weather integration (if available)
- Special events calendar
- Trend detection and adjustment

### 7. 🖥️ Admin Web UI

**Core Components:**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  TRANSIT OPS ADMIN DASHBOARD                                    [User ▼]   │
├───────────────┬─────────────────────────────────────────────────────────────┤
│               │                                                             │
│  📊 Overview  │  ┌─────────────────────────────────────────────────────┐   │
│               │  │  SERVICE HEALTH SCORE: 87/100  ▲ +3 from yesterday  │   │
│  📈 Analytics │  └─────────────────────────────────────────────────────┘   │
│               │                                                             │
│  🚌 Routes    │  ┌──────────────────┐  ┌──────────────────┐                │
│               │  │ ON-TIME: 94.2%   │  │ ACTIVE BUSES: 127│                │
│  🗺️ Map View  │  │ ▲ +1.5%          │  │ ▼ -3 from plan   │                │
│               │  └──────────────────┘  └──────────────────┘                │
│  🤖 AI Chat   │                                                             │
│               │  ┌─────────────────────────────────────────────────────┐   │
│  💡 Suggest.  │  │  LIVE HEADWAY CHART                                 │   │
│               │  │  [Real-time streaming visualization]                │   │
│  📋 Reports   │  │  ████████░░ Route 14: 8.2 min (target: 10)         │   │
│               │  │  ██████████ Route 38: 12.1 min (target: 12) ⚠️     │   │
│  ⚙️ Settings  │  │  ███████░░░ Route 22: 7.5 min (target: 8)          │   │
│               │  └─────────────────────────────────────────────────────┘   │
│  📖 Docs      │                                                             │
│               │  ┌─────────────────────────────────────────────────────┐   │
│               │  │  AI RECOMMENDATIONS (3 new)                         │   │
│               │  │  🔴 Add bus to Route 14 AM peak - High Priority     │   │
│               │  │  🟡 Reduce Route 38 midday frequency - Medium       │   │
│               │  │  🟢 Schedule shift for Route 22 - Low Priority      │   │
│               │  └─────────────────────────────────────────────────────┘   │
└───────────────┴─────────────────────────────────────────────────────────────┘
```

**UI Sections:**

| Section | Purpose |
|---------|---------|
| **Overview** | High-level KPIs, service health score, alerts |
| **Analytics** | Interactive charts, drill-down capabilities |
| **Routes** | Per-route details, historical performance |
| **Map View** | Geographic visualization of service |
| **AI Chat** | Natural language query interface |
| **Suggestions** | AI recommendations with priority |
| **Reports** | Scheduled/ad-hoc report generation |
| **Settings** | User preferences, alert thresholds |
| **Docs** | API documentation, usage guides |

**Live Elements (Low Latency):**
- Real-time headway monitoring
- Live bus positions on map
- Streaming alert feed
- Auto-refreshing KPI cards
- WebSocket-powered updates

---

## Technical Architecture

### Data Layer

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              SNOWFLAKE                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  RAW Schema (Landing Zone)                                                  │
│  ├── raw_transitapp_stops         (JSON from API)                          │
│  ├── raw_transitapp_departures    (JSON from API)                          │
│  ├── raw_gtfs_routes              (GTFS static)                            │
│  ├── raw_gtfs_stops               (GTFS static)                            │
│  └── raw_gtfs_trips               (GTFS static)                            │
│                                                                             │
│  STAGING Schema (dbt - Cleaned)                                             │
│  ├── stg_departures               (Parsed, typed, validated)               │
│  ├── stg_alerts                   (Normalized alerts)                      │
│  ├── stg_routes                   (Route dimension)                        │
│  └── stg_stops                    (Stop dimension)                         │
│                                                                             │
│  ANALYTICS Schema (dbt - Marts)                                             │
│  ├── reliability_metrics          (OTP, headway gaps, consistency)         │
│  ├── demand_metrics               (Boardings, patterns, trends)            │
│  ├── crowding_metrics             (Capacity utilization, forecasts)        │
│  ├── revenue_metrics              (Ridership revenue, cost efficiency)     │
│  └── decision_support             (Ranked recommendations)                 │
│                                                                             │
│  ML Schema (Predictions)                                                    │
│  ├── demand_forecasts             (Next 24-48h predictions)                │
│  ├── delay_forecasts              (Expected delays)                        │
│  └── crowding_forecasts           (Capacity predictions)                   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Application Layer

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           APPLICATION STACK                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  BACKEND SERVICES                                                           │
│  ├── API Server (FastAPI/Flask)                                            │
│  │   ├── /api/metrics/*          (KPI endpoints)                           │
│  │   ├── /api/routes/*           (Route data)                              │
│  │   ├── /api/predictions/*      (ML forecasts)                            │
│  │   ├── /api/suggestions/*      (AI recommendations)                      │
│  │   └── /api/chat               (Chatbot endpoint)                        │
│  │                                                                          │
│  ├── Chatbot Service                                                        │
│  │   ├── LLM Integration (OpenAI/Claude)                                   │
│  │   ├── SQL Generation                                                    │
│  │   └── Response Formatting                                               │
│  │                                                                          │
│  └── WebSocket Server (for live updates)                                   │
│      ├── Real-time metrics streaming                                       │
│      └── Alert notifications                                               │
│                                                                             │
│  FRONTEND (Admin UI)                                                        │
│  ├── Framework: React/Vue/Streamlit/Dash                                   │
│  ├── Charts: Plotly/Chart.js/D3.js                                         │
│  ├── Maps: Mapbox/Leaflet                                                  │
│  └── Real-time: WebSocket client                                           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Data Flow & Pipeline

### Real-Time Ingestion Flow

```
Every 5 minutes:
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ EventBridge  │────▶│ SQS Queue    │────▶│ Lambda       │────▶│ S3 Bucket    │
│ Trigger      │     │ (Buffer)     │     │ (Fetch API)  │     │ (Raw JSON)   │
└──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
                                                                      │
                     ┌──────────────────────────────────────────────────
                     │
                     ▼
              ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
              │ Snowpipe     │────▶│ RAW Tables   │────▶│ dbt Models   │
              │ (Auto-load)  │     │ (Snowflake)  │     │ (Transform)  │
              └──────────────┘     └──────────────┘     └──────────────┘
                                                               │
                     ┌──────────────────────────────────────────
                     │
                     ▼
              ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
              │ Analytics    │────▶│ ML Models    │────▶│ Decision     │
              │ Marts        │     │ (Predict)    │     │ Support      │
              └──────────────┘     └──────────────┘     └──────────────┘
```

### Orchestration (Airflow DAGs)

| DAG | Schedule | Purpose |
|-----|----------|---------|
| `ingestion_dag` | Every 5 min | Trigger Lambda, verify S3 landing |
| `transformation_dag` | Every 10 min | Run dbt, update marts |
| `ml_refresh_dag` | Daily 3 AM | Retrain ML models, generate forecasts |

---

## Required Technology Stack

### MUST USE (Project Requirements)

| Category | Technology | Purpose |
|----------|------------|---------|
| **Orchestration** | Apache Airflow | Workflow scheduling, DAG management |
| **Transformation** | dbt Core | SQL-based transforms, testing, docs |
| **Cloud** | AWS | Lambda, S3, SQS, EventBridge, CloudFormation |
| **Streaming** | Snowpipe + SQS | Near real-time data loading |
| **Warehouse** | Snowflake | Central data storage, ML, analytics |
| **Language** | Python | Ingestion, API, ML, chatbot |
| **Language** | SQL | dbt models, analytics queries |
| **Visualization** | BI Tool | Dashboards (Snowsight/QuickSight/Custom) |
| **UI** | Web Framework | Admin interface (React/Streamlit/Dash) |

### Technology Choices

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  INGESTION & ORCHESTRATION                                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│  • AWS Lambda (Python 3.9+) - Serverless API calls                          │
│  • AWS EventBridge - Scheduled triggers                                     │
│  • AWS SQS - Message queuing, buffering                                     │
│  • AWS S3 - Raw data lake storage                                           │
│  • Apache Airflow - Workflow orchestration                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│  DATA WAREHOUSE & TRANSFORMATION                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│  • Snowflake - Cloud data warehouse                                         │
│  • Snowpipe - Auto-ingest from S3                                           │
│  • dbt Core - Transform, test, document                                     │
│  • Snowflake ML - Built-in ML capabilities                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│  APPLICATION & UI                                                            │
├─────────────────────────────────────────────────────────────────────────────┤
│  • Python FastAPI - Backend API                                             │
│  • Perplexity API - LLM for chatbot (Sonar model)                           │
│  • React + Vite + Tailwind - Admin UI                                       │
│  • Recharts - Interactive charts                                            │
│  • React-Leaflet - Interactive maps                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│  BI & VISUALIZATION                                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│  • Snowsight - Native Snowflake BI (free)                                   │
│  • QuickSight - AWS BI (optional)                                           │
│  • Custom Python Charts - Embedded in UI                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│  INFRASTRUCTURE                                                              │
├─────────────────────────────────────────────────────────────────────────────┤
│  • AWS CloudFormation - Infrastructure as Code                              │
│  • Docker - Local development                                               │
│  • Git - Version control                                                    │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Current Project Status

### 📊 Latest Test Results (November 26, 2025)

```
============================================================
LOCAL TESTING SUMMARY
============================================================

✅ TransitApp API Ingestion
   - API Key: Valid and working
   - Nearby Stops: 149 stops fetched (San Francisco area)
   - Departures: 40 departures across 4 routes (Civic Center BART)
   - Data saved to: ingestion/data/local_test/transitapp/

✅ GTFS Feed Sync
   - BART: Downloaded and validated successfully
   - Caltrain: Disabled (can be enabled if needed)
   - Data saved to: ingestion/data/local_test/gtfs/BART/

✅ dbt Project
   - Connection: OK (Snowflake connected)
   - Account: sfedu02-lvb17920
   - Database: USER_DB_HORNET
   - Warehouse: HORNET_QUERY_WH
   - Models: 4 staging + 5 analytics models ready

✅ Chatbot API
   - Flask app: Imports successfully
   - Ready for integration

✅ Snowflake Connection
   - Status: Connected
   - Existing Schemas: ANALYTICS, RAW, TRANSFORM, STAGE, etc.
   - Transit Tables: NOT YET CREATED (needs Phase 1)

❌ NOT YET DONE
   - AWS cloud deployment (Phase 5)
============================================================
```

### ✅ Completed

| Component | Status | Notes |
|-----------|--------|-------|
| Project Structure | ✅ Done | Full directory structure in place |
| Configuration | ✅ Done | `secrets.yaml`, `master_config.yaml` |
| TransitApp API Ingestion | ✅ Done | Lambda code, tested locally (149 stops, 40 departures) |
| GTFS Sync | ✅ Done | BART feed working |
| Local Testing Script | ✅ Done | `test_ingestion_local.py` verified |
| dbt Project Setup | ✅ Done | 4 staging + 5 analytics models |
| dbt Snowflake Connection | ✅ Done | Verified working |
| Snowflake Schema SQL | ✅ Done | SQL scripts ready |
| AWS CloudFormation | ✅ Done | IaC template ready |
| Airflow DAGs | ✅ Done | 3 DAGs defined |
| Dashboard SQL | ✅ Done | Snowsight queries ready |
| Documentation | ✅ Done | README, ARCHITECTURE, CONTEXT.md |
| **Snowflake Data Loading** | ✅ Done | 80 departures, 298 stops, 4 routes, 8 alerts |
| **Kafka Streaming** | ✅ Done | Docker setup, producer/consumer scripts |
| **Dynamic Tables** | ✅ Done | Real-time aggregation tables |
| **dbt Analytics** | ✅ Done | 9 models (staging + analytics) |
| **React Admin UI** | ✅ Done | Dashboard, Routes, Map, Forecasts, Chat |
| **FastAPI Backend** | ✅ Done | Snowflake endpoints, chat endpoint |
| **LLM Integration** | ✅ Done | Perplexity AI (Sonar model) |
| **Chatbot** | ✅ Done | Natural language queries, SQL generation |
| **Unit Tests** | ✅ Done | Phase 1 (17/17), Phase 2 (14/14), LLM (4/4) |

### 🔄 Development Phases (One at a Time)

We work on **ONE PHASE AT A TIME**. Complete testing before moving to next.

---

## 🎯 PHASED DEVELOPMENT PLAN

### Phase 1: Snowflake Schema & Data Loading ✅ COMPLETED
**Goal**: Get transit data into Snowflake so dbt can transform it

| Task | Status | Description |
|------|--------|-------------|
| 1.1 Create Landing Tables | ✅ Done | RAW.TRANSIT_DEPARTURES, STOPS, ALERTS, GTFS_FEEDS, ROUTES |
| 1.2 Update dbt Sources | ✅ Done | sources.yml + incremental staging models |
| 1.3 Create Data Loader | ✅ Done | scripts/load_data_to_snowflake.py |
| 1.4 Setup Kafka | ✅ Done | kafka/docker-compose.yml + producer/consumer |
| 1.5 Dynamic Tables SQL | ✅ Done | snowflake/setup/02_dynamic_tables.sql |
| 1.6 Load & Verify | ✅ Done | 80 departures, 298 stops, 4 routes, 8 alerts |
| **Phase 1 Testing** | ✅ | dbt run --select staging = 4/4 PASSED |

### Phase 2: dbt Models & Analytics Marts ✅ COMPLETED
**Goal**: Transform raw data into analytics-ready marts

| Task | Status | Description |
|------|--------|-------------|
| 2.1 Install dbt_utils | ✅ Done | Added packages.yml, ran dbt deps |
| 2.2 Update analytics models | ✅ Done | Fixed column names, added metrics |
| 2.3 Run all dbt models | ✅ Done | 9/9 models passed |
| 2.4 Create unit tests | ✅ Done | tests/test_phase2_analytics.py |
| 2.5 Run tests | ✅ Done | 14/14 tests passed |
| **Phase 2 Testing** | ✅ | dbt PASS=9, Unit Tests PASS=14 |

### Phase 3: Admin UI (Dashboard + Chatbot + Visualizations) ✅ COMPLETED
**Goal**: Build the internal admin web application

| Task | Status | Description |
|------|--------|-------------|
| 3.1 React + Vite + Tailwind | ✅ Done | Modern React app with dark transit theme |
| 3.2 Build layout | ✅ Done | Sidebar nav, header with city selector, main content |
| 3.3 KPI cards | ✅ Done | On-time %, active routes, alerts, revenue |
| 3.4 Live charts | ✅ Done | Headway chart, demand bars, pie chart (Recharts) |
| 3.5 Chatbot placeholder | ✅ Done | DataQuery page with demo mode |
| 3.6 Route explorer | ✅ Done | Route selector, AI insights, hourly charts |
| 3.7 Map View | ✅ Done | Leaflet map with SF transit stops |
| 3.8 Forecasts page | ✅ Done | 6h/24h/7d toggle with charts |
| 3.9 BI Dashboard embed | ✅ Done | Tableau/PowerBI placeholder |
| 3.10 FastAPI Backend | ✅ Done | api/main.py with Snowflake endpoints |
| 3.11 Docker setup | ✅ Done | Dockerfile + docker-compose.yml |
| **Phase 3 Testing** | ✅ | UI runs at localhost:3000, all pages work |

**Key Features Built:**
- City selector (SF, NYC, Toronto, Montreal, London, Paris, Berlin, Sydney)
- Developer credits: "Ayush Gawai" in sidebar, footer, map, forecasts
- Severity indicators: 🟢🟡🔴 for route health
- Tooltips with proper dark theme styling
- Real Leaflet map with transit stops
- Forecast buttons that switch data views

### Phase 4: LLM Integration & AI Insights ✅ COMPLETED
**Goal**: Connect LLM to chatbot for natural language data queries

| Task | Status | Description |
|------|--------|-------------|
| 4.1 LLM API setup | ✅ Done | Perplexity API (Sonar model) connected |
| 4.2 Snowflake context | ✅ Done | Full schema context in api/llm/schema_context.py |
| 4.3 SQL generation | ✅ Done | LLM generates queries from questions |
| 4.4 Severity indicators | ✅ Done | 🟢🟡🔴 thresholds defined (90%/75%) |
| 4.5 Off-topic handling | ✅ Done | Redirects non-transit questions |
| 4.6 Integration in UI | ✅ Done | Chat UI connected to FastAPI backend |
| **Phase 4 Testing** | ✅ | 4/4 tests passed (connection, chat, DB, severity) |

**LLM Integration Details:**
- **API**: Perplexity AI (Sonar model)
- **Files Created**:
  - `api/llm/__init__.py` - Module exports
  - `api/llm/perplexity_client.py` - API client
  - `api/llm/schema_context.py` - Snowflake schema for LLM
  - `api/llm/chat_handler.py` - Main chat logic
  - `tests/test_llm_integration.py` - Integration tests
- **Features**:
  - ✅ **Direct answers** - No follow-up prompts (non-technical user friendly)
  - ✅ **SQL hidden** - Technical details abstracted from users
  - ✅ **Data context** - Live Snowflake data provided to LLM
  - ✅ Severity analysis (🟢🟡🔴)
  - ✅ Off-topic question redirection
  - ✅ Error handling with developer contact info
  - ✅ **"i" buttons powered by LLM** - All info buttons fetch AI insights
  - ✅ `/api/insights` endpoint for route/chart/metric analysis

### Phase 5: AWS Cloud Deployment (Optional/Future)
**Goal**: Deploy to production cloud infrastructure

| Task | Status | Description |
|------|--------|-------------|
| 5.1 Deploy CloudFormation | ⬜ Pending | Create AWS resources |
| 5.2 Configure Snowpipe | ⬜ Pending | S3 → Snowflake auto-ingest |
| 5.3 Deploy Lambda | ⬜ Pending | API ingestion functions |
| 5.4 Deploy UI | ⬜ Pending | Host on EC2/ECS/Amplify |
| **Phase 5 Testing** | ⬜ | End-to-end cloud pipeline works |

---

### 📋 Current Priority

| Priority | Component | Description |
|----------|-----------|-------------|
| ✅ DONE | Phase 1 | Snowflake schema + data loading |
| ✅ DONE | Phase 2 | dbt models & analytics |
| ✅ DONE | Phase 3 | Admin UI (React Dashboard) |
| ✅ DONE | Phase 4 | LLM Integration & AI Insights |
| **NEXT** | Phase 5 | AWS cloud deployment |

### 📅 Progress Log

| Date | Phase | Milestone |
|------|-------|-----------|
| Nov 25, 2025 | Phase 1 | Snowflake tables, Kafka, data loaded - 17/17 tests passed |
| Nov 25, 2025 | Phase 2 | dbt analytics models - 14/14 tests passed |
| Nov 26, 2025 | Phase 3 | React UI complete with 7 pages, Leaflet map, FastAPI backend |
| Nov 26, 2025 | Phase 4 | Starting LLM integration... |

---

## Project Structure

```
transit-system/
├── CONTEXT.md                   # THIS FILE - Project context for AI/team
├── README.md                    # Project overview and quick start
├── ARCHITECTURE.md              # Technical architecture details
├── DEPLOYMENT_CHECKLIST.md      # Step-by-step deployment guide
├── EXTENSION_ROADMAP.md         # Future enhancements
├── requirements.txt             # Python dependencies
├── secrets.yaml                 # Credentials (NOT in git)
│
├── config/
│   └── master_config.yaml       # Configuration template
│
├── infrastructure/
│   └── cloudformation.yaml      # AWS IaC template
│
├── ingestion/
│   ├── lambda/
│   │   ├── transit_api_ingestion.py   # TransitApp API Lambda
│   │   ├── gtfs_sync.py               # GTFS download Lambda
│   │   ├── config_loader.py           # Config utilities
│   │   └── utils.py                   # Shared utilities
│   ├── test_ingestion_local.py        # Local test script
│   └── data/local_test/               # Local test data output
│
├── snowflake/
│   ├── setup/
│   │   ├── schema.sql                 # Database schema DDL
│   │   ├── snowpipe.sql               # Snowpipe configuration
│   │   └── permissions.sql            # Role/permission grants
│   └── ml/
│       └── demand_forecast.py         # ML model definitions
│
├── dbt/
│   └── transit_dbt/
│       ├── dbt_project.yml            # dbt configuration
│       ├── profiles.yml               # Snowflake connection
│       └── models/
│           ├── staging/               # Staging models
│           │   ├── stg_departures.sql
│           │   ├── stg_alerts.sql
│           │   ├── stg_routes.sql
│           │   └── stg_stops.sql
│           └── analytics/             # Analytics marts
│               ├── reliability_metrics.sql
│               ├── demand_metrics.sql
│               ├── crowding_metrics.sql
│               ├── revenue_metrics.sql
│               └── decision_support.sql
│
├── airflow/
│   ├── docker-compose.yml             # Local Airflow setup
│   └── dags/
│       ├── ingestion_dag.py           # Data ingestion DAG
│       ├── transformation_dag.py      # dbt transformation DAG
│       └── ml_refresh_dag.py          # ML model refresh DAG
│
├── ui/                                # React Admin Dashboard
│   ├── package.json                   # Node dependencies
│   ├── vite.config.ts                 # Vite build config
│   ├── tailwind.config.js             # Tailwind CSS theme
│   ├── Dockerfile                     # Production container
│   └── src/
│       ├── App.tsx                    # Main app routes
│       ├── components/Layout.tsx      # Sidebar + header
│       └── pages/
│           ├── Dashboard.tsx          # Main KPIs, charts
│           ├── Routes.tsx             # Route explorer
│           ├── Analytics.tsx          # Deep analytics
│           ├── MapView.tsx            # Leaflet map
│           ├── Forecasts.tsx          # ML predictions
│           ├── DataQuery.tsx          # Chatbot UI
│           └── BIDashboard.tsx        # BI embed
│
├── api/                               # FastAPI Backend
│   ├── main.py                        # API endpoints
│   ├── requirements.txt               # Python deps
│   └── Dockerfile                     # Production container
│
├── dashboard/
│   ├── DASHBOARD_SPEC.md              # Dashboard specifications
│   └── snowsight_queries/             # SQL for Snowsight
│       ├── reliability_dashboard.sql
│       ├── demand_crowding_dashboard.sql
│       ├── forecasting_dashboard.sql
│       ├── revenue_dashboard.sql
│       └── decision_support_dashboard.sql
│
├── chatbot/
│   ├── chatbot_api.py                 # Flask API endpoint
│   └── README.md                      # Chatbot documentation
│
├── ui/                                # [TO BE CREATED]
│   ├── app.py                         # Streamlit/Dash app
│   ├── components/                    # UI components
│   ├── static/                        # CSS, JS, assets
│   └── templates/                     # HTML templates
│
├── scripts/
│   ├── load_secrets.sh                # Load secrets to env
│   └── load_env.sh                    # Environment setup
│
└── venv/                              # Python virtual environment
```

---

## Deliverables & Milestones

### Phase 1: Data Pipeline (Foundation)
- [x] Local ingestion testing
- [ ] AWS Lambda deployment
- [ ] S3 + SQS + EventBridge setup
- [ ] Snowflake database creation
- [ ] Snowpipe configuration
- [ ] dbt models execution
- [ ] Basic data validation

### Phase 2: Analytics & Visualization
- [ ] Reliability metrics mart
- [ ] Demand/crowding metrics
- [ ] Snowsight dashboards
- [ ] Custom Python visualizations
- [ ] Historical trend analysis

### Phase 3: AI & Intelligence
- [ ] Chatbot improvements
- [ ] AI recommendation engine
- [ ] Fleet optimization logic
- [ ] ML forecasting models
- [ ] Decision support table

### Phase 4: Admin UI
- [ ] UI framework setup
- [ ] Dashboard integration
- [ ] Chatbot interface
- [ ] AI suggestions panel
- [ ] Real-time updates
- [ ] Documentation pages

### Phase 5: Polish & Deploy
- [ ] End-to-end testing
- [ ] Performance optimization
- [ ] Security review
- [ ] Documentation finalization
- [ ] Demo preparation

---

## KPIs & Success Metrics

### Technical KPIs

| Metric | Target | How to Measure |
|--------|--------|----------------|
| Ingestion Latency | < 30 seconds | Time from API call to S3 landing |
| Data Freshness | < 2 minutes | Time from event to queryable in Snowflake |
| Gap Detection Accuracy | ≥ 95% | Correctly identify gaps >10 min |
| Chatbot Response Time | < 3 seconds | End-to-end query to response |
| Dashboard Load Time | < 2 seconds | Page load with data |
| System Uptime | 99.5% | Lambda success rate |

### Business Value KPIs (Simulated)

| Metric | Description |
|--------|-------------|
| Service Health Score | Composite reliability score (0-100) |
| Fleet Efficiency | % of buses at optimal utilization |
| Gap Reduction | % decrease in headway gaps |
| Prediction Accuracy | ML forecast vs. actual |
| Time Saved | Ops team decision time reduced |

---

## Future Enhancements

### Near-Term (If Time Permits)
- Weather data integration for demand adjustment
- Special events calendar integration
- Email/Slack alerting for anomalies
- PDF report generation
- API rate limiting and caching

### Long-Term (Post-Project)
- Mobile companion app for ops
- Rider-facing service status page
- Multi-agency federation
- Reinforcement learning for dynamic scheduling
- Real-time passenger push notifications
- Dynamic demand-based pricing

---

## Quick Reference

### Running Local Tests
```bash
cd /Users/spartan/Documents/MSDA/Project/transit-system
source venv/bin/activate
python ingestion/test_ingestion_local.py
```

### Key Files
| Purpose | File |
|---------|------|
| Secrets | `secrets.yaml` |
| Config | `config/master_config.yaml` |
| Ingestion | `ingestion/lambda/transit_api_ingestion.py` |
| dbt Models | `dbt/transit_dbt/models/` |
| Dashboards | `dashboard/snowsight_queries/` |
| Chatbot | `chatbot/chatbot_api.py` |

### API Endpoints (TransitApp)
- Base URL: `https://external.transitapp.com/v3`
- Nearby Stops: `/public/nearby_stops`
- Departures: `/public/stop_departures`
- Rate Limit: 5 calls/min, 1500 calls/month

### Snowflake Schemas
- `RAW` - Landing zone for raw JSON
- `STAGING` - Cleaned, typed data
- `ANALYTICS` - Mart tables for BI
- `ML` - Predictions and forecasts

### Important Credentials Location
All credentials stored in `secrets.yaml` (not in git):
- Snowflake: Account, user, password, warehouse
- TransitApp: API key
- AWS: Access keys, region
- OpenAI: API key (for chatbot)

---

## Notes for AI Assistants

When working on this project:

1. **Always check `secrets.yaml`** for credentials before suggesting config changes
2. **The project uses dbt Core** (not dbt Cloud) - all dbt commands run locally
3. **Snowflake is the central warehouse** - all analytics queries go there
4. **TransitApp API has strict rate limits** - 5 calls/min, respect this
5. **The Admin UI is not yet built** - this is a key upcoming deliverable
6. **Local testing works** - use `test_ingestion_local.py` to verify changes
7. **AWS resources are not yet deployed** - CloudFormation stack needs to be created
8. **BART is the primary transit agency** for testing (SF Bay Area)

### IMPORTANT CLARIFICATIONS:

9. **We are DATA ENGINEERS, not business advisors**
   - We provide DATA and METRICS, not recommendations
   - Business team makes decisions based on our data
   - The `decision_support` table provides metrics, NOT recommendations
   
10. **LLM Integration (Future)**
    - When we add LLM, it will analyze data and show severity indicators
    - Red/Yellow/Green based on severity, impact, money saved
    - NOT making business recommendations, just highlighting data patterns
    
11. **Everything must be DEPLOYABLE**
    - Nothing stays local - all components must work in AWS
    - Design for cloud deployment from the start
    
12. **UI Must Be UNIQUE and BEAUTIFUL**
    - Not a generic dashboard
    - Transit-themed, modern, dark mode
    - Professional quality for internal ops team

---

## 🚨 WHERE WE LEFT OFF

### Session: November 26, 2025 (Latest)

**✅ PHASE 1 COMPLETED (17/17 tests passed):**
- ✅ Created landing tables in RAW schema
- ✅ Updated dbt staging models with proper sources
- ✅ Created data loader script + Kafka setup
- ✅ Loaded test data to Snowflake
- ✅ All staging models working

**✅ PHASE 2 COMPLETED (14/14 tests passed):**
- ✅ Installed dbt_utils package
- ✅ Updated all 5 analytics models
- ✅ Ran all 9 dbt models - ALL PASSED!
- ✅ Created Phase 2 unit tests
- ✅ Verified metrics calculations

**📊 Data in Snowflake:**
```
RAW Layer:
  TRANSIT_DEPARTURES: 2 rows
  TRANSIT_STOPS: 2 rows  
  TRANSIT_GTFS_FEEDS: 8 rows

Staging Layer:
  STG_DEPARTURES: 80 rows
  STG_STOPS: 298 rows
  STG_ROUTES: 4 rows
  STG_ALERTS: 8 rows

Analytics Layer:
  reliability_metrics: 15 rows
  demand_metrics: 4 rows
  crowding_metrics: 15 rows
  revenue_metrics: 4 rows
  decision_support: 4 recommendations
```

**Sample Analytics Results:**
- Route Blue: 100% on-time, reliability score 100
- Total estimated revenue: $14,087.50
- AI Recommendation: "INCREASE_FREQUENCY" (priority=75)

**Next Session Should Start With:**
1. Read this CONTEXT.md
2. Start **Phase 3: Admin UI (Dashboard + Chatbot)**

---

## 📝 PHASE 1 COMPLETED - What Was Built

### Files Created in Phase 1:

| File | Purpose |
|------|---------|
| `snowflake/setup/01_landing_tables.sql` | Landing tables + Stream |
| `snowflake/setup/02_dynamic_tables.sql` | Dynamic Tables for streaming |
| `dbt/transit_dbt/models/sources.yml` | dbt source definitions |
| `dbt/transit_dbt/models/staging/stg_*.sql` | Updated incremental models |
| `scripts/load_data_to_snowflake.py` | Data loader script |
| `kafka/docker-compose.yml` | Kafka Docker setup |
| `kafka/transit_producer.py` | API → Kafka producer |
| `kafka/transit_consumer.py` | Kafka → Snowflake consumer |
| `kafka/README.md` | Kafka documentation |

### Tables Created:

```
RAW.TRANSIT_DEPARTURES     - Real-time departures (VARIANT)
RAW.TRANSIT_STOPS          - Stop reference data
RAW.TRANSIT_ALERTS         - Service alerts  
RAW.TRANSIT_GTFS_FEEDS     - Static GTFS data
RAW.TRANSIT_ROUTES         - Route info
RAW.TRANSIT_DEPARTURES_STREAM - CDC Stream
```

### Streaming Options:

1. **Kafka** (kafka/docker-compose.yml)
   - Run: `cd kafka && docker-compose up -d`
   - UI: http://localhost:8090

2. **Dynamic Tables** (02_dynamic_tables.sql)
   - Auto-refresh on data change
   - Pause to save costs: `ALTER DYNAMIC TABLE ... SUSPEND;`

---

## 🛠️ USEFUL COMMANDS

### Run Local Ingestion Test
```bash
cd /Users/spartan/Documents/MSDA/Project/transit-system
source venv/bin/activate
python ingestion/test_ingestion_local.py
```

### Set Environment Variables
```bash
export SNOWFLAKE_ACCOUNT="sfedu02-lvb17920"
export SNOWFLAKE_USER="HORNET"
export SNOWFLAKE_PASSWORD="Ayush123456789"
export SNOWFLAKE_WAREHOUSE="HORNET_QUERY_WH"
export SNOWFLAKE_DATABASE="USER_DB_HORNET"
export SNOWFLAKE_ROLE="TRAINING_ROLE"
```

### Run dbt
```bash
cd dbt/transit_dbt
dbt debug    # Test connection
dbt run      # Run all models
dbt test     # Run tests
```

### Start Chatbot (Local)
```bash
cd chatbot
python chatbot_api.py
```

---

*This document serves as the single source of truth for project context. Update it as the project evolves.*

**Last Updated**: November 26, 2025

