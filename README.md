# FinSight – AI-Driven Cloud Cost & Security Intelligence

## Project Overview

**FinSight** is a unified AI-driven observability platform designed to tackle the dual challenges of **uncontrolled cloud spending (FinOps)** and **identity security (SecOps)**. Current cloud management solutions are often fragmented, creating disconnects between financial efficiency and system security. FinSight addresses this by integrating four specialized machine learning engines to proactively monitor, predict, secure, and optimize cloud resources in real-time.

The platform bridges the gap between financial operations and security by correlating cost anomalies with security risks. It features a modern **React-based "Glass Pane" dashboard** for unified visualization and a robust **FastAPI backend** that simulates a live cloud environment. Key innovations include **Zero Trust behavioral biometrics**, **Explainable AI (XAI)** for anomaly root cause analysis, and **Risk-Aware Optimization** with self-healing deployment simulations.

- **GitHub Repository:** (https://github.com/subodhi01/Research_Project)
- **Live Demo:** (https://drive.google.com/drive/folders/1WH8dbiEV1r9RC_apvGbRgHN1wX9nmIw4?usp=drive_link)

---

## System Architecture

The system follows a **Microservices-lite architecture**, orchestrated by a central API Gateway. It separates the frontend user experience from the heavy computational logic of the four core AI engines.

### High-level Architecture Components:


* **Frontend:** React SPA (Single Page Application) for interactive dashboards and biometric data capture.
* **Backend:** FastAPI services handling request routing, authentication, and core business logic.
* **AI/ML Engines:** Four distinct analytical modules for Security, Anomaly Detection, Forecasting, and Optimization.
* **Simulation Layer:** A `psutil`-based service that mocks real-time cloud metrics (CPU, RAM, Network) to enable research testing without incurring actual cloud costs.
* **Storage:** SQLite/SQLAlchemy for structured data persistence.

### Architecture Diagram
Image Link - https://drive.google.com/drive/folders/1WH8dbiEV1r9RC_apvGbRgHN1wX9nmIw4?usp=drive_link

---

## Technology Stack & Dependencies

### Frontend
* **React.js:** Component-based UI library for dynamic dashboards.
* **Tailwind CSS:** Utility-first framework for modern, responsive styling.
* **Recharts:** Composable charting library for visualizing time-series forecasts and anomalies.
* **Axios:** HTTP client for API communication and intercepting JWT tokens.

### AI / Machine Learning
* **Scikit-Learn:** Core ML algorithms (Isolation Forest, Random Forest, SGD Classifier).
* **Statsmodels:** ARIMA models for time-series forecasting.
* **PyTorch / TensorFlow:** (Optional) Used for autoencoder-based anomaly detection.
* **Pandas & NumPy:** Data manipulation and feature engineering.

### Backend & Core Services
* **FastAPI:** High-performance async web framework.
* **SQLAlchemy:** ORM for database interactions.
* **SQLite:** Lightweight relational database for research prototyping.
* **Psutil:** System monitoring library used to simulate cloud resource usage.
* **PyJWT:** Handling JSON Web Tokens for secure authentication.

---

## 1. Predictive Cloud Budgeting & Forecasting System
> **Developed by: [RATHNAYAKA W.S.A.A. - IT22364456D]**

This component addresses the challenge of budget overruns by predicting future cloud spending. It utilizes time-series forecasting to project future costs and enables dynamic "What-If" scenario planning for financial decision-making.

### Workflow
1.  **Historical Data Analysis:** Loads and processes historical cost and resource usage data.
2.  **Workload-Aware Forecasting:** Utilizes **ARIMA** (AutoRegressive Integrated Moving Average) models combined with exogenous variables (such as Day of Week) to predict spending trends, accounting for seasonal patterns like weekend dips.
3.  **Budget Risk Assessment:** Integrates the forecast curve to calculate the **"Projected Delta"** against the predefined monthly budget.
4.  **Scenario Planning:** Provides an interactive interface where users can adjust variables (e.g., *"Growth +20%"*, *"Savings +10%"*) to instantly recalculate budget risk and financial projections.

### Technologies Used
* **Statsmodels (ARIMA):** Statistical modeling library for accurate time-series forecasting.
* **Pandas:** Used for complex time-series indexing and resampling operations.
* **Recharts:** For visualizing "Actual" vs. "Forecast" trend lines with confidence intervals.

### Future Development
In the future, the proposed system will extend its capabilities beyond checking a single VPS to connect directly with AWS. To improve predictive accuracy, the model will be upgraded from ARIMA to SARIMA, which allows for the use of more parameters. By improving the dataset through this live integration, the system will be able to provide much more precise financial forecasts.


**Deployment:** **Deployment:** [http://158.220.115.171:8000/api/forecast/runs]
                                [http://158.220.115.171:8000/api/forecast/department/forecast]

---

## 2. Cloud Cost & Resource Anomaly Detection System
> **Developed by: [KARUNARATHNA S.N.W. - IT22916976]**

This component focuses on the early detection of irregularities in cloud infrastructure. It moves beyond static threshold alerts to detect complex, multi-variate outliers in cost and resource usage using Unsupervised Learning techniques.

### Workflow
1.  **Metric Ingestion:** The system ingests real-time metrics including CPU utilization, memory usage, load averages, and daily cost.
2.  **Detection Logic:**
    * **Isolation Forest:** Detects multidimensional anomalies (e.g., high cost occurring during low traffic periods).
    * **Z-Score Analysis:** Flags immediate statistical spikes that deviate significantly from the mean.
    * **Autoencoder:** Identifies subtle anomalies by measuring high reconstruction errors in neural network outputs.
3.  **Explainability Service:** The engine performs feature contribution analysis to generate human-readable root cause explanations (e.g., *"Anomaly driven by 400% spike in Disk I/O"*).
4.  **Visualization:** Anomalies are plotted on the dashboard with calculated severity levels (**Critical** / **Warning** / **Info**).

### Technologies Used
* **Isolation Forest (Unsupervised Learning):** For robust outlier detection in high-dimensional data.
* **Feature Contribution Analysis:** Logic algorithms to translate mathematical anomaly scores into descriptive text.
* **FastAPI Background Tasks:** To process detection streams asynchronously without blocking the user interface.

### Future Development
In the future, the Anomaly Detection Engine will expand beyond its current training set of 14,440 records by integrating large-scale, real-world production data or authoritative external datasets to enhance model robustness. This richer data foundation will enable the deployment of complex multi-model ensembles, while current static thresholds will be replaced by dynamic, adaptive mechanisms that automatically tune sensitivity to historical volatility. By leveraging these authentic datasets and adaptive techniques, the system will significantly reduce false positives and ensure superior accuracy across dynamic cloud environments.

**Deployment:** [http://158.220.115.171:8000/api/anomaly/detect/iforest]


---

## 3. Intelligent Resource Optimization & Rightsizing Engine
> **Developed by: [DAHANAYAKA O.M.S. - IT22915672]**

This component aims to reduce cloud waste by recommending precise rightsizing actions. Uniquely, it operates as a **"Risk-Aware"** system, ensuring that cost-saving measures do not compromise system stability.

### Workflow
1.  **Resource Analysis:** Continuously analyzes utilization patterns to classify resources as Idle, Underutilized, or Overutilized.
2.  **Recommendation Generation:** Uses a **Random Forest Classifier** to determine the optimal action (Upsize, Downsize, or Shutdown) based on historical performance data.
3.  **Risk-Adjusted Ranking:** Recommendations are ranked based on a composite score derived from *Savings Potential* versus *Stability Risk*.
4.  **Simulated Canary Deployment:** Upon user approval:
    * The backend tentatively simulates the configuration change.
    * It monitors metrics for immediate performance degradation (latency or error rates).
    * If instability is detected, an **Automatic Rollback** is triggered to preserve system availability.

### Technologies Used
* **Random Forest Classifier:** Supervised learning algorithm for decision-making and classification.
* **Simulation Logic:** Custom Python logic to mock deployment states, latency injection, and rollback triggers.
* **Interactive UI:** Dashboard controls for "One-Click Deploy" with real-time status feedback.

### Future Development
Reduction of Model Retraining Interval
In future work, the continuous training interval of the Random Forest model will be reduced from one hour to fifteen minutes. This enhancement will allow the system to respond more rapidly to dynamic workload changes and cost fluctuations in cloud environments.

**Deployment:** [http://158.220.115.171:8000/api/optimize/retrain]


---

## 4. Zero Trust Behavioral Authentication System
> **Developed by: [MALLIKAHEWA S.R. - IT22324924]**

This component replaces static password trust with continuous behavioral verification. It analyzes biometric patterns to ensure that the user interacting with the system is the legitimate account owner.

### Workflow
1.  **Biometric Data Capture:** The Frontend securely captures behavioral data during login, including:
    * Typing Speed (WPM).
    * Flight Time (latency between keystrokes).
    * Contextual data (Browser tabs, Timezone, CapsLock usage).
2.  **Risk Scoring:** The encrypted payload is sent to the backend where an **SGD Classifier** (Logistic Regression) calculates a real-time "Risk Score" (0.0 to 1.0).
3.  **Access Decision:**
    * **Low Risk:** Login proceeds normally.
    * **High Risk:** Login is blocked (403 Forbidden), and the event is logged for security auditing.
4.  **Admin Observability:** Administrators can access a "Real-time Login Events" panel to review specific risk factors (e.g., *"Unusually fast typing detected"*).

### Technologies Used
* **SGD Classifier:** Linear classifier optimized for high-dimensional sparse data to predict risk probability.
* **JWT (JSON Web Tokens):** Claims-based authentication enriched with dynamic risk scores.
* **Heuristics Engine:** Rule-based fallback checks (e.g., flagging bot-like typing speeds > 150 WPM).

### Future Development
1. Create a unique 'digital fingerprint' for each user based on their habits, allowing the system to instantly block hackers because they don't behave like the real owner.
2. The system will automatically block login attempts from suspicious locations or unauthorized countries and immediately alert the administrator.

**Deployment:** [http://158.220.115.171:8000/api/zero-trust/score-session]

