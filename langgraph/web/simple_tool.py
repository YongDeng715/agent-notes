from langchain_community.document_loaders import WebBaseLoader
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.tools.retriever import create_retriever_tool
import os
import yaml

urls = [
    "https://lilianweng.github.io/posts/2023-06-23-agent/",
    "https://lilianweng.github.io/posts/2023-03-15-prompt-engineering/",
    "https://lilianweng.github.io/posts/2023-10-25-adv-attack-llm/",
]

docs = [WebBaseLoader(url).load() for url in urls]
docs_list = [item for sublist in docs for item in sublist]

text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
    chunk_size=100, chunk_overlap=50
)
doc_splits = text_splitter.split_documents(docs_list)

# Add to vectorDB
vectorstore = Chroma.from_documents(
    documents=doc_splits,
    collection_name="rag-chroma",
    embedding=OpenAIEmbeddings(),
)
retriever = vectorstore.as_retriever()


retriever_tool = create_retriever_tool(
    retriever,
    "retrieve_blog_posts",
    "Search and return information about Lilian Weng blog posts on LLM agents, prompt engineering, and adversarial attacks on LLMs.",
)

# Aggregate all retrieval tools for agent use
tools = [retriever_tool]

# Load OpenAI API key for embeddings from conf.yaml
CONF_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', 'twitter-agent', 'conf.yaml')
with open(CONF_PATH, 'r', encoding='utf-8') as f:
    conf = yaml.safe_load(f)
openai_key = conf.get('OPENAI_EMBEDDING', {}).get('api_key')
if openai_key:
    os.environ['OPENAI_API_KEY'] = openai_key
