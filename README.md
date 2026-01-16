# Image-Monitoring-Anomaly-Detection-System-Microservices-
A Dockerized microservices-based image monitoring system that allows users to upload images into categorized folders and continuously compares them against CCTV inputs to detect visual anomalies in near real time.

🔍 Overview

This project implements an end-to-end image monitoring pipeline using Flask, Python workers, Redis, and Docker Compose. It is designed to simulate real-world scenarios such as CCTV validation, industrial monitoring, or security checks, where uploaded reference images are continuously compared with live camera feeds.

🧱 Architecture

The system consists of three core services:

Upload Service (Flask)
A web-based interface that allows users to upload images into six predefined folders and exposes REST APIs to retrieve the latest image per folder.

Retriever Service (Background Worker)
Periodically fetches the latest uploaded images, compares them against the latest CCTV images using perceptual hashing, and raises alerts when visual differences exceed a configurable threshold.

Redis
Acts as a lightweight in-memory data store for alert states and similarity metrics, enabling decoupled service communication and future extensibility.

🔁 Workflow

User uploads images via the Flask web interface.

Images are stored in folders on disk.

The retriever service polls for the latest uploaded image per folder.

The retriever compares it with the latest CCTV image.

Alerts are triggered and stored in Redis when discrepancies are detected.

🧠 Image Comparison

Uses Perceptual Hashing (pHash) to compare visual similarity

Robust to resizing, lighting, and compression differences

Configurable similarity threshold (default: 0.9)

🐳 Tech Stack

Python

Flask

Redis

Docker & Docker Compose

Pillow & imagehash

🚀 Running Locally
docker-compose up --build


Upload UI: http://localhost:5000

Retriever logs: docker logs -f retriever_service

🚨 Alerting

Alerts are logged in real time

Stored in Redis under keys like alert_folder1

Similarity scores stored under similarity_folderX

🎯 Use Cases

CCTV validation & monitoring

Industrial process verification

Visual quality control

Security anomaly detection

Computer vision pipeline prototyping

🔮 Future Enhancements

Real-time alert dashboard

RTSP camera ingestion

Slack / Email notifications

ML-based anomaly detection

Cloud deployment (AWS / GCP / Azure)
