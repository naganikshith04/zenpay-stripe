print("LOADING MAIN.PY")
# zenpay_backend/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import customers, usage, credits, webhooks, products, subscriptions
from .core.config import settings
from .db.models import Base
from .db.session import engine


with open("main_loaded.log", "w") as f:
    f.write("main.py has been loaded\n")

Base.metadata.create_all(bind=engine)
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="API for usage-based billing with Stripe",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Set up CORS
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Include routers
app.include_router(usage.router, prefix="/api/v1/usage", tags=["usage"])
app.include_router(customers.router, prefix="/api/v1/customers", tags=["customers"])
app.include_router(credits.router, prefix="/api/v1/credits", tags=["credits"])
app.include_router(webhooks.router, prefix="/api/v1/webhooks", tags=["webhooks"])
app.include_router(products.router, prefix="/api/v1/products", tags=["products"])
app.include_router(subscriptions.router, prefix="/api/v1/subscriptions", tags=["subscriptions"])

@app.get("/health", tags=["system"])
def health_check():
    """
    Health check endpoint
    """
    return {"status": "healthy"}

@app.get("/", tags=["system"])
def root():
    """
    Root endpoint
    """
    return {
        "message": f"Welcome to {settings.PROJECT_NAME} API",
        "docs": "/docs",
        "redoc": "/redoc"
    }