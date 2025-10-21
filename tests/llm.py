from prazo.utils.chat_models import ChatModel

def test_chat_model():
    openai_chat_model = ChatModel(provider="openai", model_name="gpt-4o-mini")
    google_chat_model = ChatModel(provider="google", model_name="gemini-2.5-flash")
    deepseek_chat_model = ChatModel(provider="deepseek", model_name="deepseek-chat")
    
    print(openai_chat_model.llm())
    print(google_chat_model.llm())
    print(deepseek_chat_model.llm())
    
if __name__ == "__main__":
    test_chat_model()