"""Latencia de endpoints de la API local (p50/p95/p99 y peticiones por segundo).

Uso (desde backend/, con la API corriendo):
    uv run python scripts/bench_api.py [--base http://127.0.0.1:8000] [--n 500] [--concurrency 10]
Imprime filas Markdown para docs/environment/resultados/.
"""

import argparse
import asyncio
import statistics
import time

import httpx

ENDPOINTS = ("/health", "/health/ready")


async def bench(client: httpx.AsyncClient, path: str, n: int, concurrency: int) -> str:
    latencies: list[float] = []
    errors = 0
    sem = asyncio.Semaphore(concurrency)

    async def one() -> None:
        nonlocal errors
        async with sem:
            start = time.perf_counter()
            response = await client.get(path)
            latencies.append((time.perf_counter() - start) * 1000)
            errors += response.status_code != 200

    for _ in range(20):  # calentamiento: conexiones y pool de BD
        await client.get(path)
    wall = time.perf_counter()
    await asyncio.gather(*(one() for _ in range(n)))
    wall = time.perf_counter() - wall
    q = statistics.quantiles(latencies, n=100)
    return (
        f"| `{path}` | {n} | {concurrency} | {q[49]:.1f} | {q[94]:.1f} | {q[98]:.1f} "
        f"| {n / wall:.0f} | {errors} |"
    )


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="http://127.0.0.1:8000")
    parser.add_argument("--n", type=int, default=500)
    parser.add_argument("--concurrency", type=int, default=10)
    args = parser.parse_args()

    print("| Endpoint | Peticiones | Concurrencia | p50 ms | p95 ms | p99 ms | req/s | Errores |")
    print("|---|---|---|---|---|---|---|---|")
    async with httpx.AsyncClient(base_url=args.base, timeout=10) as client:
        for path in ENDPOINTS:
            print(await bench(client, path, args.n, args.concurrency))


if __name__ == "__main__":
    asyncio.run(main())
