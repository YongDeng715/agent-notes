import os
import yaml
from langchain_openai import ChatOpenAI

def get_llm_config(section="BASIC_MODEL"):
    CONF_PATH = os.path.join(os.path.dirname(__file__), 'conf.yaml')
    if not os.path.exists(CONF_PATH):
        CONF_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'conf.yaml')
    with open(CONF_PATH, 'r', encoding='utf-8') as f:
        conf = yaml.safe_load(f)
    model_conf = conf.get(section, {})
    return {
        'base_url': model_conf.get('base_url'),
        'model_name': model_conf.get('model'),
        'api_key': model_conf.get('api_key'),
    }

def get_chat_openai(section="BASIC_MODEL", **kwargs):
    conf = get_llm_config(section)
    return ChatOpenAI(
        base_url=conf['base_url'],
        api_key=conf['api_key'],
        model_name=conf['model_name'],
        **kwargs
    ) 