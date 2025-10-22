from pprint import pprint as pp

from prazo.utils.deduplication import deduplicate
from prazo.schemas import NewsItem

def test_deduplication():
    articles = [
        NewsItem(
            title="OpenAI Announces Major Breakthrough in Artificial Intelligence with Launch of Advanced GPT-5 Language Model Featuring Enhanced Reasoning Capabilities",
            summary="OpenAI has officially unveiled GPT-5, marking a significant milestone in artificial intelligence development. The new language model demonstrates unprecedented capabilities in complex reasoning, mathematical problem-solving, and contextual understanding. According to OpenAI CEO Sam Altman, GPT-5 represents a fundamental leap forward in AI technology, with the ability to process and understand nuanced information at levels previously thought impossible. The model has been trained on an extensive dataset encompassing scientific literature, programming code, and multilingual content. Early testing shows remarkable improvements in accuracy, with error rates reduced by over 40% compared to its predecessor. The release has generated considerable excitement within the tech community, with researchers praising its potential applications in healthcare, education, and scientific research. Industry experts suggest this advancement could accelerate the development of more sophisticated AI systems across various sectors.",
            sources=["https://techcrunch.com/2025/10/20/openai-gpt5-announcement", "https://openai.com/blog/gpt5-release"],
            published_date="2025-10-20",
            topic="Artificial Intelligence",
            groups=["Technology", "AI Research"],
            tool_source="brave_search"
        ),
        NewsItem(
            title="GPT-5 Released by OpenAI: Revolutionary AI System Demonstrates Superior Performance in Logical Reasoning and Problem Solving Tasks Across Multiple Domains",
            summary="In a groundbreaking announcement today, OpenAI introduced GPT-5, their latest and most advanced artificial intelligence model to date. The new system showcases dramatic improvements in logical reasoning and analytical thinking, particularly excelling in complex problem-solving scenarios that challenged previous versions. Sam Altman, CEO of OpenAI, described the release as a transformative moment for the AI industry. The model has undergone rigorous testing across multiple domains including mathematics, science, coding, and natural language understanding. Preliminary benchmarks indicate that GPT-5 achieves accuracy levels that surpass GPT-4 by significant margins, with particular strengths in maintaining context over longer conversations and generating more coherent, factually accurate responses. The technology incorporates novel training techniques and architectural improvements that enable better comprehension of abstract concepts. Researchers and developers are already exploring potential applications ranging from medical diagnosis assistance to advanced educational tools. The AI community has responded with enthusiasm, viewing this as a pivotal advancement in machine learning capabilities.",
            sources=["https://theverge.com/ai/2025/10/20/openai-launches-gpt5", "https://reuters.com/technology/openai-gpt5-2025"],
            published_date="2025-10-20",
            topic="Artificial Intelligence",
            groups=["Technology", "AI Research"],
            tool_source="ddg_search"
        ),
        NewsItem(
            title="Global Climate Summit Reaches Historic Agreement on Carbon Emissions Reduction with Participation from Over 150 Countries Committing to Net Zero by 2050",
            summary="World leaders have achieved a landmark agreement at the Global Climate Summit held in Geneva, with representatives from more than 150 nations pledging concrete actions to combat climate change. The comprehensive accord sets ambitious targets for reducing carbon emissions, with participating countries committing to achieve net-zero emissions by 2050. The agreement includes specific provisions for transitioning away from fossil fuels, investing in renewable energy infrastructure, and protecting biodiversity. Developed nations have agreed to provide substantial financial support to help developing countries meet their climate goals, with a commitment of $500 billion in climate financing over the next decade. Environmental scientists have hailed the agreement as a crucial step forward, though many emphasize the need for immediate implementation and accountability mechanisms. The accord also addresses deforestation, ocean conservation, and sustainable agriculture practices. UN Secretary-General António Guterres called it the most significant climate action agreement since the Paris Climate Accord, expressing cautious optimism about humanity's ability to address the climate crisis.",
            sources=["https://bbc.com/news/world-climate-summit-2025", "https://un.org/climatechange/geneva-summit"],
            published_date="2025-10-21",
            topic="Climate Change",
            groups=["Environment", "Politics"],
            tool_source="brave_search"
        ),
    ]
    deduplicated_articles = deduplicate(articles)
    print(len(deduplicated_articles))
    for article in deduplicated_articles:
        print(article.title)
        print(article.summary)
        print(article.sources)
        print(article.published_date)
        print(article.topic)
        print(article.groups)
        print(article.tool_source)
        print("-"*100)

if __name__ == "__main__":
    test_deduplication()