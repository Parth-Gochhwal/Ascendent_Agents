# Ascendent Agents (NEXUS) — Quick Start Guide

Welcome! This guide will help you run the NEXUS project locally with minimal effort. 

## Prerequisites
Before you begin, ensure you have the following installed on your machine:
- **Python 3.11+**
- **Node.js and npm**
- Make sure you have downloaded or cloned this repository to your local machine.

---

## Run the Project

You will need two separate terminal windows.

### Terminal 1: Start the Backend

From the repository root, activate the virtual environment and start the backend server:

```powershell
.\.venv\Scripts\Activate.ps1
python -m uvicorn backend.app.main:app --reload
```

### Terminal 2: Start the Frontend

In a new terminal window, navigate to the frontend directory and start the development server:

```powershell
cd frontend
npm run dev
```

---

## Open the Application

Once both servers are running, open your web browser and navigate to:

- **NEXUS Interface**: [http://localhost:5173](http://localhost:5173)
- **Backend API Documentation**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## Demo Mode

**Note**: The application is configured to run in **Demo Mode** by default. You can seamlessly explore the complete research pipeline and UI using the synthetic research corpus without needing to configure any API keys or secrets.

Enjoy your testing! The NEXUS interface will open in your browser, ready to demonstrate its autonomous research capabilities.
