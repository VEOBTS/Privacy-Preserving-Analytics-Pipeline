from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.api.routes import router
from app.db.database import engine
from app.db.models import Base
from app.core.crypto import load_or_generate_keys
from app.core.scheduler import start_scheduler
import logging

# Set up logging so you can see what the server is doing
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s  %(name)s  %(levelname)s  %(message)s'
)

app = FastAPI(
    title='Privacy-Preserving Analytics API',
    description='Aggregated analytics using Paillier homomorphic encryption',
    version='1.0.0'
)

# CORS configuration
# In development, allow all origins.
# In production, replace '*' with your actual frontend domain.
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

# Include all routes from routes.py
app.include_router(router)


@app.on_event('startup')
async def startup_event():
    """
    Runs once when the server starts.
    Order is important: create tables, load keys, start scheduler.
    """
    # Create database tables if they do not exist
    Base.metadata.create_all(bind=engine)
    logging.info('Database tables created/verified')

    # Load or generate the Paillier keypair
    load_or_generate_keys()

    # Start the background aggregation scheduler
    start_scheduler()


# Serve the client SDK JavaScript file as a static file
# So any website can include it with <script src='http://your-server/sdk/analytics.js'>
import os
SDK_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'client-sdk')
if os.path.exists(SDK_PATH):
    app.mount('/sdk', StaticFiles(directory=SDK_PATH), name='sdk')