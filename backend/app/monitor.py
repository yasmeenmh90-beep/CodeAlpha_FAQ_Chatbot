from collections import deque
from threading import Lock
from time import perf_counter, time

events = deque(maxlen=500)
lock = Lock()
started = time()

async def monitor(request, call_next):
    begin = perf_counter()
    status = 500
    try:
        response = await call_next(request)
        status = response.status_code
        return response
    finally:
        route = request.scope.get("route")
        path = getattr(route, "path", "unmatched")
        if path.startswith("/api/") and path != "/api/monitor":
            with lock:
                events.append({"time": time(), "method": request.method, "route": path,
                               "status": status, "latency_ms": round((perf_counter()-begin)*1000, 2)})

def snapshot():
    with lock:
        rows = list(events)
    n = len(rows)
    times = sorted(r["latency_ms"] for r in rows)
    return {"uptime_seconds": int(time()-started), "requests": n,
            "errors": sum(r["status"] >= 400 for r in rows),
            "mean_latency_ms": round(sum(times)/n, 2) if n else None,
            "p95_ms": times[max(0, (95*n+99)//100-1)] if n else None,
            "events": rows[::-1]}
