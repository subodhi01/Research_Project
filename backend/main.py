from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import Base, engine
from .anomaly_engine import router as anomaly
from .forecasting_budget import router as forecast
from .optimization_engine import router as optimize
from .finsight_dashboard.monitor_router import router as monitor
from .finsight_dashboard.insight_router import router as insight
from .finsight_dashboard.ux_router import router as ux
from .zero_trust import router as zero_trust
from .routers import auth

app = FastAPI()

Base.metadata.create_all(bind=engine)

origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://cloudcost.space",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(anomaly)
app.include_router(forecast)
app.include_router(optimize)
app.include_router(monitor)
app.include_router(insight)
app.include_router(ux)
app.include_router(zero_trust)
app.include_router(auth.router)


@app.get("/")
async def root():
    return {"status": "ok"}
