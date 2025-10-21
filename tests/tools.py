from prazo.utils.tools import tavily_search_tool, wikipedia_search_tool, arxiv_search_tool, ddg_search_tool


def test_tavily_search_tool():
    tool = tavily_search_tool()
    print(tool.invoke({"query": "What happened at the last wimbledon"}))


def test_wikipedia_search_tool():
    tool = wikipedia_search_tool()
    print(tool.invoke({"query": "What happened at the last wimbledon"}))
    
def test_arxiv_search_tool():
    tool = arxiv_search_tool()
    print(tool.invoke({"query": "What happened at the last wimbledon"}))
    
def test_ddg_search_tool():
    tool = ddg_search_tool()
    print(tool.invoke({"query": "What happened at the last wimbledon"}))

def main():
    # test_tavily_search_tool()
    # test_wikipedia_search_tool()
    # test_arxiv_search_tool()
    test_ddg_search_tool()
if __name__ == "__main__":
    main()