# FlightAware Mimic API

This project is a Python (FastAPI) application that mimics the core functionality of a flight tracking service like FlightAware. It uses MongoDB to store and manage live flight data and archive completed flights.

## Features

-   **Backend**: Python with [FastAPI](https://fastapi.tiangolo.com/).
-   **Database**: MongoDB, using two collections to manage the data lifecycle:
    -   `live_flights`: For active, in-progress flights.
    -   `completed_flights_log`: For archiving flight data after landing.
-   **Data Ingestion**: A `POST /ingest` API to mimic radio signals and add location points to a flight's track.
-   **Data Lifecycle**: An API (`POST /flights/{flight_id}/complete`) to move data from the live collection to the log collection.
-   **Tracking API**: A `GET /track/{flight_id}` API to retrieve the full path of any flight (live or completed).
-   **Bonus Map**: A `GET /track/{flight_id}/map` endpoint that generates and returns a live, interactive [Folium](https://python-visualization.github.io/folium/) map of the flight's path.

---

## Setup and Execution Instructions

### 1. Prerequisites

-   **Python 3.8+**
-   **MongoDB**: A running MongoDB server on `mongodb://localhost:27017/`.

### 2. Setup Virtual Environment

Create and activate a virtual environment.

```bash
# Create the project folder and 'cd' into it
mkdir flight-aware-mimic
cd flight-aware-mimic

# Create and activate venv
python -m venv venv
# On macOS/Linux:
source venv/bin/activate
# On Windows (cmd):
.\venv\Scripts\activate
```

### 3. Install Dependencies

Install all required packages (including `folium` for the map).

```bash
pip install -r requirements.txt
```

### 4. Run the Project

#### Step 1: Start MongoDB
Ensure your MongoDB server is running.

#### Step 2: Seed the Database
Run the seeder script to populate your `live_flights` collection with sample scheduled flights.

```bash
python scripts/seed_db.py
```

You should see an output confirming 3 records were inserted into `live_flights`.

#### Step 3: Start the API Server
Run the FastAPI application using `uvicorn`.

```bash
uvicorn app.main:app --reload
```
The server will start on `http://127.0.0.1:8000`.

---

## API Testing & Example Workflow

Your API is now live. Open the interactive documentation at:

**<http://127.0.0.1:8000/docs>**

### 1. Send "Radio Signals" (Ingest Data)

Let's make flight `PK303` take off.

-   Go to `POST /ingest`.
-   Click "Try it out".
-   Use this as the request body to send the **first ping**:

```json
{
  "flight_id": "PK303",
  "timestamp": "2026-01-10T09:15:00Z",
  "latitude": 31.5204,
  "longitude": 74.3587,
  "altitude": 10000,
  "speed": 180
}
```
-   Click **Execute**. The response will show the flight status is now "EN-ROUTE" and the `track` array has one point.

-   Now send a **second ping** (e.g., 15 mins later):

```json
{
  "flight_id": "PK303",
  "timestamp": "2026-01-10T09:30:00Z",
  "latitude": 31.7204,
  "longitude": 74.1587,
  "altitude": 32000,
  "speed": 450
}
```
-   Click **Execute**. The `track` array will now have two points.

### 2. Track the Flight (View Full Track)

-   Go to `GET /track/{flight_id}`.
-   Click "Try it out".
-   Enter `PK303` for the `flight_id`.
-   Click **Execute**.
-   The response will show the full flight details, with the two location points in the `track` array.

### 3. View the **BONUS MAP**

-   Open a new browser tab and go directly to this URL:
    **<http://127.0.0.1:8000/track/PK303/map>**
-   You will see an interactive map with a blue line connecting your two data points.

### 4. Mark the Flight as "Landed" (Archive)

-   Go to `POST /flights/{flight_id}/complete`.
-   Click "Try it out".
-   Enter `PK303` for the `flight_id`.
-   Click **Execute**.
-   The response will show the full flight, now with status "LANDED".
-   If you use **MongoDB Compass**, you will see that `PK303` is **gone** from `live_flights` and **is now** in `completed_flights_log`