from fastapi import FastAPI, Request
import uvicorn

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "🚀 Hello! Your FastAPI bot is running!"}

@app.post("/")
async def receive_webhook(req: Request):
    data = await req.json()
    print("Received webhook:", data)
    return {"status": "received"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)
