import hashlib
import os
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import uvicorn

app = FastAPI(title="Exam MCP Server")

NORMALIZED_EMAIL = "24ds2000042@ds.study.iitm.ac.in".strip().lower()

@app.get("/")
@app.get("/health")
async def health():
    return {"status": "ok", "service": "mcp-server"}

@app.post("/")
@app.post("/mcp")
@app.post("/sse")
async def mcp_endpoint(request: Request):
    headers = {k.lower(): v for k, v in request.headers.items()}
    try:
        body = await request.json()
    except Exception:
        body = {}

    req_id = body.get("id")
    method = body.get("method", "")

    # 1. MCP Handshake: initialize
    if method == "initialize":
        return JSONResponse({
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {"listChanged": False}
                },
                "serverInfo": {
                    "name": "exam-mcp-server",
                    "version": "1.0.0"
                }
            }
        })

    # 2. MCP Handshake: initialized notification
    if method in ["notifications/initialized", "initialized"]:
        if req_id is not None:
            return JSONResponse({"jsonrpc": "2.0", "id": req_id, "result": {}})
        return JSONResponse({"status": "acknowledged"})

    # 3. Tool Discovery: list tools
    if method == "tools/list":
        return JSONResponse({
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "tools": [
                    {
                        "name": "solve_challenge",
                        "description": "Solves challenge by hashing header",
                        "inputSchema": {
                            "type": "object",
                            "properties": {}
                        }
                    }
                ]
            }
        })

    # 4. Tool Execution: read X-Exam-Challenge header and compute SHA-256
    if method == "tools/call":
        challenge = headers.get("x-exam-challenge", "")

        # Compute SHA-256("${challenge}:${normalizedEmail}")[:16]
        raw_token = f"{challenge}:{NORMALIZED_EMAIL}"
        answer = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()[:16]

        return JSONResponse({
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "content": [
                    {
                        "type": "text",
                        "text": answer
                    }
                ],
                "isError": False
            }
        })

    return JSONResponse({"jsonrpc": "2.0", "id": req_id, "result": {}})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
