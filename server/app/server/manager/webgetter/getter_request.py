from app.server.manager.data.generator_cache import ProcessGeneratorCache


class WebGetterRequest:
    def __init__(self, hub_uuid: str, app_id_list: list, auth: dict or None,
                 use_cache: bool = True, cache_data: bool = True):
        self.queue = ProcessGeneratorCache()

        self.hub_uuid: str = hub_uuid
        self.app_id_list = app_id_list
        self.auth = auth

        self.use_cache = use_cache
        self.cache_data = cache_data
