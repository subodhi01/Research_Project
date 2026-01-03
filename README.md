# Research_Project
# CloudCost - Intelligent Cloud Cost Management Platform

A comprehensive cloud cost management and optimization platform with AI-powered forecasting, anomaly detection, budget intelligence, and zero-trust security features.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)
![React](https://img.shields.io/badge/React-18.3-blue.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## 🚀 Features

### 📊 Forecasting & Budget Intelligence
- **ARIMA Time Series Forecasting**: Predict future cloud costs using statistical models
- **Budget Comparison**: Compare forecasts against budgets with risk alerts
- **Department Allocation**: Allocate budgets across departments with predictive analytics
- **Scenario Planning**: Test multiple budget scenarios (what-if analysis)
- **Budget Recommendations**: Get budget suggestions based on company size and historical data

### 🔍 Anomaly Detection
- **Real-time Anomaly Detection**: Identify unusual cost patterns using Isolation Forest and statistical methods
- **Multi-metric Analysis**: Monitor CPU, memory, and cost anomalies
- **Alert System**: Automated alerts for detected anomalies
- **Historical Analysis**: Track anomaly patterns over time

### ⚡ Optimization Engine
- **Resource Optimization**: ML-powered recommendations for cost savings
- **Right-sizing Suggestions**: Optimize instance types and configurations
- **Cost Reduction Strategies**: Identify opportunities to reduce cloud spending
- **Performance Metrics**: Track optimization impact

### 🔐 Zero Trust Security
- **Password Security Analysis**: ML-based password strength assessment
- **Login Risk Scoring**: Evaluate login attempts for security risks
- **Supervised Learning Models**: Advanced security threat detection
- **User Behavior Analysis**: Monitor and analyze user access patterns

### 📈 Monitoring & Insights
- **Real-time Monitoring**: Live dashboard for cloud resource usage
- **Multi-cloud Support**: Monitor VPS and AWS resources
- **Department Tracking**: Track costs and usage by department
- **Interactive Dashboards**: Beautiful, responsive UI with charts and visualizations

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Frontend (React)                        │
│  - React 18.3 with React Router                            │
│  - Recharts for data visualization                          │
│  - Tailwind CSS for styling                                 │
│  - Axios for API communication                              │
└────────────────────┬────────────────────────────────────────┘
                     │ REST API
┌────────────────────▼────────────────────────────────────────┐
│                   Backend (FastAPI)                         │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Forecasting & Budget Engine                          │  │
│  │  - ARIMA time series forecasting                      │  │
│  │  - Budget allocation & comparison                     │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Anomaly Detection Engine                             │  │
│  │  - Isolation Forest ML model                          │  │
│  │  - Statistical anomaly detection                      │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Optimization Engine                                  │  │
│  │  - ML-based optimization recommendations              │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Zero Trust Security                                  │  │
│  │  - Password security analysis                         │  │
│  │  - Login risk scoring                                │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│                    Data Layer                                │
│  - SQLite Database (cloudcost.db)                           │
│  - CSV Datasets (historical data)                           │
│  - AWS Cost Explorer API                                     │
└─────────────────────────────────────────────────────────────┘
```

## 📋 Prerequisites

- **Python**: 3.8 or higher
- **Node.js**: 16.x or higher
- **npm** or **yarn**: Package manager
- **AWS Account** (optional): For AWS cost integration
- **SQLite**: Included with Python

## 🛠️ Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd cloudcost
```

### 2. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment (Linux/Mac)
python3 -m venv venv
source venv/bin/activate

# Create virtual environment (Windows)
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r ../requirements.txt
```

### 3. Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install
```

### 4. Database Setup

The database will be automatically created on first run. The SQLite database file `cloudcost.db` will be created in the project root.

## 🚀 Running the Application

### Start Backend Server

```bash
# From backend directory
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

API Documentation (Swagger UI): `http://localhost:8000/docs`

### Start Frontend Development Server

```bash
# From frontend directory
cd frontend
npm start
```

The frontend will be available at `http://localhost:3000`

## 📁 Project Structure

```
cloudcost/
├── backend/                          # Backend API (FastAPI)
│   ├── anomaly_engine/               # Anomaly detection module
│   │   ├── router.py                 # API routes
│   │   ├── services_ml.py            # ML models (Isolation Forest)
│   │   └── services_cloud_dataset.py # Dataset services
│   ├── forecasting_budget/            # Forecasting & budget module
│   │   ├── router.py                 # API routes
│   │   ├── services.py               # ARIMA forecasting services
│   │   ├── services_dataset.py       # CSV dataset services
│   │   └── Cloud Budget Dataset/     # Historical cost datasets
│   ├── optimization_engine/          # Optimization module
│   │   ├── router.py                 # API routes
│   │   ├── services_ml.py             # ML optimization models
│   │   └── train_optimization_model.py # Model training
│   ├── zero_trust/                   # Zero trust security module
│   │   ├── router.py                 # API routes
│   │   ├── services.py               # Security analysis
│   │   └── train_zero_trust_supervised.py # ML model training
│   ├── finsight_dashboard/            # Dashboard module
│   │   ├── monitor_router.py         # Monitoring endpoints
│   │   ├── insight_router.py         # Insights endpoints
│   │   └── ux_router.py              # UX tracking endpoints
│   ├── routers/                      # Additional API routes
│   │   ├── auth.py                   # Authentication
│   │   ├── forecast.py               # Forecast endpoints
│   │   ├── monitor.py                # Monitoring endpoints
│   │   └── optimize.py               # Optimization endpoints
│   ├── main.py                       # FastAPI application entry point
│   ├── database.py                   # Database configuration
│   ├── models.py                     # SQLAlchemy models
│   ├── aws_client.py                 # AWS API client
│   └── services_monitor.py           # Monitoring services
│
├── frontend/                         # Frontend application (React)
│   ├── src/
│   │   ├── api/                      # API client functions
│   │   │   ├── forecast.js           # Forecast API
│   │   │   ├── anomaly.js            # Anomaly API
│   │   │   ├── optimize.js           # Optimization API
│   │   │   └── zeroTrust.js          # Security API
│   │   ├── components/               # React components
│   │   │   ├── forecasting-budget/   # Forecast panel
│   │   │   ├── anomaly-engine/       # Anomaly panel
│   │   │   ├── optimization-engine/  # Optimization panel
│   │   │   ├── zero-trust/           # Security panel
│   │   │   └── finsight-dashboard/   # Dashboard components
│   │   ├── App.jsx                   # Main app component
│   │   └── index.jsx                 # Entry point
│   ├── package.json                  # Frontend dependencies
│   └── webpack.config.js             # Webpack configuration
│
├── reports/                          # Model performance reports
│   └── model_metrics/                # ML model metrics (PNG charts)
│
├── logs/                             # Application logs
│
├── cloudcost.db                      # SQLite database (created on first run)
├── requirements.txt                  # Python dependencies
└── README.md                         # This file
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the backend directory (optional):

```env
# AWS Configuration (optional)
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key

# Alert Webhook (optional)
ALERT_WEBHOOK_URL=https://your-webhook-url.com

# Database (defaults to SQLite)
DATABASE_URL=sqlite:///./cloudcost.db
```

### Department Configuration

Edit `backend/services_monitor.py` to configure departments:

```python
DEPARTMENTS = ["HR", "IT", "Dev", "Management"]

DEPARTMENT_ALLOCATIONS = {
    "Dev": 0.40,        # 40% of budget
    "IT": 0.30,         # 30% of budget
    "HR": 0.20,         # 20% of budget
    "Management": 0.10  # 10% of budget
}
```

## 📚 API Documentation

### Forecast & Budget Endpoints

- `POST /api/forecast/ingest/vps` - Ingest VPS costs
- `POST /api/forecast/ingest/aws` - Ingest AWS costs
- `GET /api/forecast/usage` - Get cost forecast
- `GET /api/forecast/budget` - Compare forecast to budget
- `GET /api/forecast/budget/allocation` - Get department allocations
- `GET /api/forecast/scenarios` - Test budget scenarios
- `POST /api/forecast/budget/recommendation` - Get budget recommendation

### Anomaly Detection Endpoints

- `GET /api/anomaly/detect` - Detect anomalies
- `GET /api/anomaly/alerts` - Get anomaly alerts
- `POST /api/anomaly/threshold` - Set anomaly thresholds

### Optimization Endpoints

- `GET /api/optimize/recommendations` - Get optimization recommendations
- `POST /api/optimize/apply` - Apply optimization

### Zero Trust Endpoints

- `POST /api/zero-trust/analyze-password` - Analyze password security
- `POST /api/zero-trust/login-event` - Analyze login event
- `GET /api/zero-trust/risk-scores` - Get risk scores

Full API documentation available at `http://localhost:8000/docs` when the server is running.

## 🧪 Machine Learning Models

### ARIMA Forecasting Model
- **Location**: `backend/forecasting_budget/services.py`
- **Model Type**: ARIMA(1,1,1)
- **Training**: On-demand (trains when forecast is requested)
- **Data Source**: Database (cloud_usage table) or CSV datasets
- **Metrics**: MAE, RMSE, MAPE

### Isolation Forest Anomaly Detection
- **Location**: `backend/anomaly_engine/services_ml.py`
- **Model Type**: Isolation Forest (unsupervised)
- **Purpose**: Detect cost and usage anomalies

### Optimization ML Model
- **Location**: `backend/optimization_engine/services_ml.py`
- **Purpose**: Generate cost optimization recommendations

### Zero Trust Security Model
- **Location**: `backend/zero_trust/services.py`
- **Model Type**: Supervised learning (classification)
- **Purpose**: Password security and login risk assessment

## 📊 Data Sources

### Database (SQLite)
- **File**: `cloudcost.db`
- **Tables**:
  - `cloud_usage`: Daily cost and usage metrics
  - `forecast_runs`: Forecast results and metrics
  - `budget_alerts`: Budget alerts
  - `anomaly_alerts`: Anomaly alerts
  - `recommendations`: Optimization recommendations

### CSV Datasets
- **Location**: `backend/forecasting_budget/Cloud Budget Dataset/`
- **Files**:
  - `cloud_budget_2023_dataset.csv` - Main historical dataset
  - `cloud_budget_2023_dataset_daily_account_summary.csv`
  - `cloud_budget_2023_dataset_monthly_account_summary.csv`

### External APIs
- **AWS Cost Explorer API**: For fetching AWS costs
- **VPS Metrics**: CPU and memory usage from VPS instances

## 🎯 Usage Examples

### Generate Forecast

```python
# Via API
GET /api/forecast/usage?horizon_days=30&provider=vps

# Response
{
  "run_id": 123,
  "mae": 5.2,
  "rmse": 7.8,
  "mape": 4.5,
  "history": [...],
  "forecast": [...]
}
```

### Compare to Budget

```python
# Via API
GET /api/forecast/budget?monthly_budget=3000&horizon_days=30

# Response
{
  "budget": 3000.0,
  "projected_total": 3200.0,
  "delta": 200.0,
  "status": "over_budget_risk",
  "metrics": {...}
}
```

### Detect Anomalies

```python
# Via API
GET /api/anomaly/detect?window_hours=24&provider=vps

# Response
{
  "items": [
    {
      "resource_id": "vps-01",
      "metric": "cost",
      "value": 500.0,
      "anomaly_score": 0.95,
      "severity": "high"
    }
  ]
}
```

## 🧪 Testing

### Backend Tests

```bash
cd backend
pytest tests/
```

### Frontend Tests

```bash
cd frontend
npm test
```

## 📈 Model Performance Reports

Model performance metrics and visualizations are stored in `reports/model_metrics/`:
- Forecast accuracy metrics (MAE, RMSE, MAPE)
- Anomaly detection performance (Precision, Recall, F1)
- Optimization model metrics
- Zero trust security model metrics

## 🚢 Deployment

### Using PM2 (Process Manager)

```bash
# Install PM2
npm install -g pm2

# Start application
pm2 start ecosystem.config.js
```

### Docker (Coming Soon)

```bash
docker-compose up -d
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **FastAPI** - Modern Python web framework
- **React** - UI library
- **statsmodels** - ARIMA time series models
- **scikit-learn** - Machine learning library
- **Recharts** - Chart library for React

## 📞 Support

For issues, questions, or contributions, please open an issue on GitHub.

## 🔗 Related Documentation

- [ARIMA Training & Datasets Guide](ARIMA_TRAINING_AND_DATASETS.md) - Detailed guide on ARIMA model training and dataset locations

---

**Built with ❤️ for intelligent cloud cost management**

