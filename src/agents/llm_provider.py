from langchain_openai import ChatOpenAI, OpenAIEmbeddings

class OpenAILLMProvider():
    def __init__(self, api_key: str, model_name: str, temperature: float=0.0, verbose: bool=True):
        self.llm_model = ChatOpenAI(api_key=api_key, 
                                    model=model_name, 
                                    temperature=temperature, 
                                    verbose=verbose)
    
    def invoke(self, prompt) -> str:
        return self.llm_model.invoke(prompt).content
    
    def with_structured_output(self, schema):
        return self.llm_model.with_structured_output(schema)
