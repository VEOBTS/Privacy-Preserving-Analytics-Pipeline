# Privacy-First Analytics

## Overview
This project is an end-to-end MVP for a secure, privacy-first analytics system that allows data to be encrypted on the client side and aggregated on the server without exposing any individual user data.

It measures content engagement without storing any individual user data. Each user's browser encrypts their behavior locally before it leaves their device. The server receives only ciphertext it cannot read, but uses additive homomorphic encryption to sum all scrambled values and decrypt only the final aggregate. This ensures that no individual record is ever visible anywhere. Before encrypting, random differential privacy noise is added to the data.

The focus of this project is on real-world privacy engineering, secure data pipelines, and scalable system design using Paillier Homomorphic Encryption and Differential Privacy.

## Project Structure
The project consists of three main components:
- **Backend (FastAPI & PostgreSQL):** Handles key distribution, receives encrypted events, aggregates ciphertexts using homomorphic encryption, and periodically decrypts the aggregated results.
- **Frontend (React):** A dashboard to visualize the aggregated, decrypted analytics data.
- **Client SDK (JavaScript):** A lightweight script that platforms integrate into their site. It handles key fetching, noise addition, encryption, and submission.

## Installation and Local Setup

To run the project locally, Docker and Docker Compose are required.

1. Clone the repository:
   ```bash
   git clone <repository_url>
   cd <repository_directory>
   ```

2. Start the services using Docker Compose:
   ```bash
   docker-compose up --build
   ```

This command builds and starts the following services:
- PostgreSQL database on port 5432
- FastAPI backend on port 8000
- React frontend on port 3000

## Usage

### Client SDK Integration
Platforms can integrate the analytics by including the JavaScript SDK snippet into their site. It handles key fetching, noise addition, encryption, and submission with zero additional code on their end.

Add the following to your HTML page:

```html
<script src="http://localhost:8000/sdk/analytics.js"></script>
<script>
  // Initialize the SDK with the backend URL
  await PrivacyAnalytics.init('http://localhost:8000');

  // Track an event
  await PrivacyAnalytics.track('video_complete', 1);
</script>
```

### Viewing Analytics
Once events are tracked, the backend aggregates and decrypts the data periodically (default every 10 minutes, configurable via `AGGREGATOR_INTERVAL_SECONDS`). The decrypted aggregated data can be viewed on the React frontend dashboard at `http://localhost:3000`.
