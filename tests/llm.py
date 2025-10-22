from prazo.utils.chat_models import ChatModel
from prazo.utils.chat_models import EmbeddingModel

def test_chat_model():
    openai_chat_model = ChatModel(provider="openai", model_name="gpt-4o-mini")
    google_chat_model = ChatModel(provider="google", model_name="gemini-2.5-flash")
    deepseek_chat_model = ChatModel(provider="deepseek", model_name="deepseek-chat")
    
    print(openai_chat_model.llm())
    print(google_chat_model.llm())
    print(deepseek_chat_model.llm())
    
def test_embedding_model():
    openai_embedding_model = EmbeddingModel(provider="openai", model_name="text-embedding-3-small")
    google_embedding_model = EmbeddingModel(provider="google", model_name="text-embedding-004")
    
    print(openai_embedding_model.get_model().embed_documents(["Hello, world!"]))
    # print(google_embedding_model.get_model())
    
    
if __name__ == "__main__":
    # test_chat_model()
    test_embedding_model()