print("!!!!!!!!!! TEST HELLO WORLD Z 22 SIERPNIA !!!!!!!!!!")
from fastapi import FastAPI
app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hello World"}
