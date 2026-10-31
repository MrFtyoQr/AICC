from redis.asyncio import Redis


def create_redis(redis_url: str, timeout_s: float) -> Redis:
    return Redis.from_url(redis_url, socket_connect_timeout=timeout_s, socket_timeout=timeout_s)


async def ping(client: Redis) -> None:
    await client.ping()
