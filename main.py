from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import auth, simplify, pdf

app = FastAPI(title="Simplim Backend", version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(simplify.router, prefix="/simplify", tags=["Simplify"])
app.include_router(pdf.router, prefix="/pdf", tags=["PDF Management"])

@app.get("/")
async def root():
    return {"message": "Welcome to Simplim Backend API"} 