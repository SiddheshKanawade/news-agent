from source_config import Source, SourceConfig, SOURCE_CONFIG_MAP

class SourceService:
    """Service for fetching and parsing sources"""
    def __init__(self, source_config_map: dict[Source, SourceConfig] = SOURCE_CONFIG_MAP):
        self.source_config_map = source_config_map

    def fetch_and_parse(self) -> list[str]:
        urls_list = []
        for _, source_config in self.source_config_map.items():
            try:
                urls = source_config.parse()
                urls_list.extend(urls)
            except Exception as e:
                print(f"Error fetching and parsing {source_config.source}: {e}")
        return urls_list
    
    def process_urls(self, urls: list[str]) -> list[str]:
        """Get Article content from urls. Can add this function in parser tools. """
        pass
    

def main():
    source_service = SourceService()
    urls_list = source_service.fetch_and_parse()
    print(len(urls_list))

if __name__ == "__main__":
    main()