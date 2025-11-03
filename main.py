from fastapi import FastAPI, HTTPException, Request

app = FastAPI()

@app.get("/api/endpoint")
def get_endpoint(request: Request, param: str = None):
    # 1) "param == max" --> Return 200 and {"result": "success"}  
    if param == "max":
        return {"result": "success"}

    # 2) "param == min" --> Return 200 and {"result": "success"}
    if param == "min":
        return {"result": "success"}

    # 3) If there's an Authorization header "Bearer invalid-api-key", 
    #    return 403 Forbidden
    auth_header = request.headers.get("Authorization")
    if auth_header == "Bearer invalid-api-key":
        raise HTTPException(status_code=403, detail="Forbidden")

    # 4) If no authorization header, return 401 Unauthorized
    if auth_header is None:
        raise HTTPException(status_code=401, detail="Unauthorized")

    # If none of the above conditions match, let's treat it as a 404:
    raise HTTPException(status_code=404, detail="Not found")


@app.get("/api/nonexistent")
def get_nonexistent():
    # Return 404 Not Found
    raise HTTPException(status_code=404, detail="Non-existent endpoint")


@app.get("/api/error")
def get_error():
    # Force 500 Internal Server Error
    raise HTTPException(status_code=500, detail="Server error")
