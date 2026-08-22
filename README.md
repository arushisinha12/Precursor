# 🔺 Precursor — Signals Before Incidents

> **Small reports gain meaning when they appear together.**

Precursor is an early-warning system that detects **emerging issues in physical spaces** by combining small observations from multiple users.

Instead of waiting for a major incident or formal complaint, Precursor looks for patterns across **location, issue type, severity, number of independent users, and recency** to identify problems while they are still emerging.

---

## 🚨 Problem Statement

Many physical-world problems begin as small, isolated signals:

* A flickering light
* A water leak
* An overflowing bin
* A damaged staircase
* Increasing crowding
* A minor safety hazard

Individually, these observations may not appear urgent. However, when similar observations start appearing from multiple people in the same area, they can indicate a developing problem.

Traditional reporting systems generally react **after an incident is recognized**.

**Precursor aims to detect the pattern before the incident.**

---

## 💡 Solution

Precursor allows users to submit lightweight observations containing:

* 📝 Description
* 📷 Optional photo
* 📍 Location
* 👤 User ID

The system then:

1. Receives the observation through **FastAPI**
2. Uses **Gemini's multimodal AI** to identify issue tags and severity
3. Stores the observation in **PostgreSQL**
4. Groups related observations using issue similarity and geographic proximity
5. Calculates an **Emergence Score**
6. Generates alerts when a cluster crosses a defined threshold
7. Displays observations and alerts through the dashboard

### Core Flow

```text
User Observation
      ↓
    FastAPI
      ↓
  Gemini AI
      ↓
Tags + Severity
      ↓
 PostgreSQL
      ↓
   Clustering
      ↓
 Emergence Score
      ↓
 Green / Yellow / Red
      ↓
     Alert
```

---

## ✨ Features

### 👤 User Reporting

* Submit observations with text
* Upload optional images
* Provide geographic coordinates
* Optionally select issue categories

### 🤖 AI Analysis

Gemini analyzes the observation and extracts:

* Issue categories
* Severity score from 1–5

Supported categories include:

`lighting` · `electrical` · `water` · `plumbing` · `structural` · `cleanliness` · `overflow` · `accessibility` · `crowding` · `equipment` · `safety` · `other`

### 📍 Spatial & Issue Clustering

Related observations are grouped based on:

* Similar issue tags
* Geographic proximity

The current prototype uses a **100-meter proximity threshold**.

### 📊 Emergence Scoring

The system calculates:

```text
Emergence Score =
Observation Count
× Distinct Users
× Average Severity
× Recency Factor
```

This allows recent, repeated reports from independent users to gain more importance.

### 🚨 Alerts

Clusters are classified as:

| Score   | Status    |
| ------- | --------- |
| `< 20`  | 🟢 Green  |
| `20–50` | 🟡 Yellow |
| `> 50`  | 🔴 Red    |

### 🏢 Organization Dashboard

Organizations can:

* View reported issues
* Sort issues by severity
* Filter observations requiring review
* Review/update observations
* View active alerts

---

## 🧠 Role of AI

Gemini is **not responsible for deciding the final alert**.

Its role is to convert unstructured user input into structured information:

```text
Text + Image
     ↓
 Gemini
     ↓
Issue Tags + Severity
```

The backend then uses those signals for clustering and emergence detection.

This keeps the final alert logic **transparent and explainable**.

---

## 🏗️ Architecture

```text
                  ┌──────────────┐
                  │    User      │
                  └──────┬───────┘
                         │
                  Observation
                  Text / Photo / GPS
                         │
                         ▼
                  ┌──────────────┐
                  │   FastAPI    │
                  │  REST API    │
                  └──────┬───────┘
                         │
              ┌──────────┴──────────┐
              ▼                     ▼
       ┌─────────────┐       ┌─────────────┐
       │ Gemini API  │       │ PostgreSQL  │
       │ AI Analysis │       │  Database   │
       └──────┬──────┘       └──────┬──────┘
              │                     │
              └──────────┬──────────┘
                         ▼
                  ┌──────────────┐
                  │  Clustering  │
                  └──────┬───────┘
                         ▼
                  ┌──────────────┐
                  │   Scoring    │
                  └──────┬───────┘
                         ▼
                  ┌──────────────┐
                  │    Alerts    │
                  └──────┬───────┘
                         ▼
                  ┌──────────────┐
                  │  Dashboard   │
                  └──────────────┘
```

---

## 🛠️ Tech Stack

### Frontend / Dashboard

* Python
* Streamlit
* Folium
* Pandas

### Backend

* Python
* FastAPI
* REST APIs

### AI / ML

* Gemini API
* Multimodal text + image analysis
* Rule-based spatial clustering
* Emergence scoring

### Database

* PostgreSQL
* SQLAlchemy

### Data

* Synthetic observations for prototype demonstration

---

## 🔌 API Endpoints

### Observations

```http
POST /observations/
```

Submit a new observation for analysis.

```http
GET /observations/
```

Retrieve reported observations.

```http
PATCH /observations/{id}
```

Update review status for an observation.

### Clusters

```http
GET /clusters/
```

Retrieve detected issue clusters.

### Alerts

```http
GET /alerts/
```

Retrieve active emerging-issue alerts.

---

## ⚙️ Setup

### 1. Clone the repository

```bash
git clone <repository-url>
cd precursor
```

### 2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate
```

On Windows:

```bash
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file and provide the required database and Gemini API configuration.

Example:

```env
DATABASE_URL=<your-postgresql-url>
GEMINI_API_KEY=<your-gemini-api-key>
```

**Do not commit API keys or `.env` files to GitHub.**

### 5. Start the backend

```bash
uvicorn main:app --reload
```

The API will run on:

```text
http://localhost:8000
```

### 6. Start the dashboard

```bash
streamlit run app.py
```

The dashboard will connect to the FastAPI backend running on port `8000`.

---

## 🧪 Prototype Data

The prototype can use synthetic observations to demonstrate the complete pipeline.

Synthetic data includes:

* Multiple users
* Different issue types
* Geographic locations
* Different severity levels
* Recent observations
* Deliberately generated clusters

The synthetic observations are submitted through the **same API used by the application**, allowing the complete analysis → clustering → alert pipeline to be demonstrated.

---

## 🔮 Future Improvements

* Real-time location detection
* Authentication and user verification
* Anti-spam and duplicate-report detection
* Asynchronous AI processing
* Scalable spatial indexing
* Improved semantic clustering
* Historical trend analysis
* Human verification workflows
* Integration with maintenance/incident-response systems
* Calibration using real-world datasets

---

## 🎯 Key Idea

> **Precursor doesn't wait for an incident to become obvious. It looks for the signals that appear before it.**

**Observe → Understand → Cluster → Score → Alert**
