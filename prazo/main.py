from prazo.utils.source_service import SourceService


def main():
    print("Starting news-agent...")

    # Initialize and run source service
    source_service = SourceService()
    articles = source_service.fetch_and_parse()

    print(f"Successfully fetched {len(articles)} articles")

    # Print first few articles as sample
    if articles:
        print("\nSample articles:")
        for i, article in enumerate(articles[:3], 1):
            print(f"{i}. {article}")


if __name__ == "__main__":
    main()
