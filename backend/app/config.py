import json
import os


CONFIG_FILE = os.path.join(os.path.dirname(__file__), '..', 'config.json') # Place config.json in backend/ root


_model_configs = {}

def load_config():
    """Loads all model configurations from CONFIG_FILE into memory."""
    global _model_configs
    _model_configs = {} # Reset before loading
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                loaded_config = json.load(f)
                # Assume new format: keys are model IDs
                if isinstance(loaded_config, dict):
                    _model_configs = loaded_config
                    print(f"Loaded model configs from {CONFIG_FILE}")
                    for model_id, config in _model_configs.items():
                        url = config.get('api_url', 'None')
                        key_status = '***' if config.get('api_key') else 'None'
                        print(f"  - Model {model_id}: URL={url}, Key={key_status}")
                else:
                    print(f"Warning: Config file {CONFIG_FILE} does not contain a valid dictionary. Using empty config.")

        except json.JSONDecodeError:
            print(f"Error: Could not decode JSON from config file {CONFIG_FILE}. Using empty config.")
            _model_configs = {}
        except Exception as e:
            print(f"Error loading config file {CONFIG_FILE}: {e}. Using empty config.")
            _model_configs = {}
    else:
        print(f"Config file {CONFIG_FILE} not found. Using default empty config.")

def get_model_config(model: str):
    """返回指定模型的配置，如果不存在则返回空字典"""
    return _model_configs.get(model, {}).copy()

def get_all_configs():
    """返回所有模型的配置"""
    return _model_configs.copy()


load_config()