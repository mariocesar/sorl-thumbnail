from asgiref.sync import iscoroutinefunction, markcoroutinefunction

from sorl.thumbnail.images import source_cache


class SourceCacheMiddleware:
    """Read each source once per request where request_started cannot: ASGI before Django 6.1."""

    def __init__(self, get_response):
        self.get_response = get_response
        if iscoroutinefunction(get_response):
            markcoroutinefunction(self)

    def __call__(self, request):
        if iscoroutinefunction(self):
            return self.acall(request)
        with source_cache():
            return self.get_response(request)

    async def acall(self, request):
        with source_cache():
            return await self.get_response(request)
