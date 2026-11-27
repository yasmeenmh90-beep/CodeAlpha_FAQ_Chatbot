import asyncio
from collections import OrderedDict
from threading import Lock
from time import monotonic
from starlette.responses import JSONResponse

class RequestGuard:
    def __init__(self, app):
        self.app = app
        self.buckets = OrderedDict()
        self.lock = Lock()

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        path = scope["path"]
        method = scope["method"]
        if (method in {"POST", "PUT"} or (method == "GET" and path.startswith(("/api/admin/", "/api/monitor")))) and path.startswith("/api/"):
            cap = 5 * 1024 * 1024 if path == "/api/documents/extract" else 2 * 1024 * 1024
            limit = 10 if path.startswith(("/api/tickets", "/api/documents", "/api/playground", "/api/admin", "/api/monitor")) else 60
            key = ((scope.get("client") or ("unknown", 0))[0], path.split("/")[2])
            now = monotonic()
            with self.lock:
                start, count = self.buckets.pop(key, (now, 0))
                if now - start >= 60:
                    start, count = now, 0
                self.buckets[key] = (start, count + 1)
                if len(self.buckets) > 4096:
                    self.buckets.popitem(last=False)
            if count >= limit:
                return await JSONResponse({"detail": "Rate limit exceeded"}, 429, headers={"Retry-After": "60"})(scope, receive, send)
            if method == "GET":
                return await self.app(scope, receive, send)
            data = bytearray()
            deadline = monotonic() + 15
            while True:
                try:
                    message = await asyncio.wait_for(receive(), timeout=max(0, deadline-monotonic()))
                except asyncio.TimeoutError:
                    return await JSONResponse({"detail": "Request body timeout"}, 408)(scope, receive, send)
                if message["type"] == "http.disconnect":
                    return
                block = message.get("body", b"")
                if len(data) + len(block) > cap:
                    return await JSONResponse({"detail": "Request too large"}, 413)(scope, receive, send)
                data.extend(block)
                if not message.get("more_body", False):
                    break
            delivered = False
            original_receive = receive
            async def replay():
                nonlocal delivered
                if not delivered:
                    delivered = True
                    return {"type": "http.request", "body": bytes(data), "more_body": False}
                return await original_receive()
            receive = replay
        await self.app(scope, receive, send)
