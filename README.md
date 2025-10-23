# Capitec Transaction Aggregation System

A comprehensive, production-grade financial transaction aggregation and analytics platform built for the Capitec Graduate Program. This system provides real-time transaction data aggregation from multiple sources with an intuitive web dashboard and robust REST API.

![Python](https://img.shields.io/badge/Python-3.11-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104-green.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)

---

## 💡 Introduction

The **Capitec Transaction Aggregation System** is a production-grade platform designed to **consolidate and analyze customer financial transaction data** from multiple sources, providing **real-time analytics** and **actionable financial insights**. It is accessible via a web dashboard and a high-performance **RESTful API** powered by **FastAPI**.

---

## 📋 Table of Contents

1. [Introduction](#-introduction)
2. [Quick Setup](#-quick-setup)

---

## 🚀 Quick Setup

This section provides the fastest way to get the system running on your local machine to build and run the application. **Docker is the recommended approach** for a consistent and quick setup.

### Prerequisites

| Option | Requirement |
| :--- | :--- |
| **Docker (Recommended)** | Docker Desktop 20.10+ and Docker Compose 2.0+ |
| **Local Development** | Python 3.11+, pip, and Virtual environment support |

### Method 1: Docker (5 Minutes)

Use Docker to build and run the application in an isolated container.

```bash
# 1. Clone or download the project
git clone <repository-link-here>
cd Capitec-Transaction-Aggregation-API

# 2. Build the Docker image
docker build -t capitec-transaction-api .

# 3. Run the container and map port 8000
docker run -d -p 8000:8000 --name transaction-api capitec-transaction-api

# 4. Access the system:
# Web Dashboard: http://localhost:8000
# API Documentation: http://localhost:8000/api/docs
