# Frontend Testing Tools

This folder serves the only purpose of testing the backend API.

## How to Run

- **Interactive Chat Simulator:**
  ```bash
  python chat_simulator.py
  ```
- **Comprehensive Test Suite:**
  ```bash
  python fully_test.py
  ```
- **API Mock Tester:**
  ```bash
  python mock.py
  ```

> Make sure the backend server is running at http://127.0.0.1:8000 and you have installed the `requests` library (`pip install requests`).

## What is Tested

- **chat_simulator.py**: Provides an interactive chat interface to test the backend's AI chat and authentication features as a real user.
- **fully_test.py**: Runs a comprehensive suite of tests covering all backend API endpoints, default 6-jar system, transactions, fees, plans, user settings, and chat agent functionality.
- **mock.py**: Runs focused, scenario-based tests for individual API endpoints and workflows, including transaction lifecycle, fee and plan filters, and chat history.
