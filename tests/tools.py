from prazo.utils.tools import tavily_search_tool


def test_tavily_search_tool():
    tool = tavily_search_tool()
    print(tool.invoke({"query": "What happened at the last wimbledon"}))

def main():
    test_tavily_search_tool()

if __name__ == "__main__":
    main()