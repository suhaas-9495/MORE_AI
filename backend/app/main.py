from fastapi import FastAPI

app = FastAPI(title="NexusAI", description="AI Agent Platform")

@app.get("/")
def root():
    return {"message": "NexusAI is running!"}