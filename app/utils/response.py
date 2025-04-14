# app/utils/response.py

from fastapi.responses import JSONResponse

def success_response(data=None, message="Success"):
    return JSONResponse(
        status_code=200,
        content={
            "status": "success",
            "message": message,
            "data": data,
        },
    )

def error_response(message="An error occurred", status_code=400, details=None):
    return JSONResponse(
        status_code=status_code,
        content={
            "status": "error",
            "message": message,
            "details": details,
        },
    )
