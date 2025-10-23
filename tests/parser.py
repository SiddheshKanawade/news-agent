from prazo.utils.parser.source_service import SourceService
from pprint import pprint as pp


def test_source_service():
    source_service = SourceService()
    articles = source_service.fetch_and_parse()
    pp(articles)
    
if __name__ == "__main__":
    test_source_service()