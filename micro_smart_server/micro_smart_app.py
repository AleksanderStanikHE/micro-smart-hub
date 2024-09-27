import os
import sys

current_dir = os.getcwd()
repo_root = os.path.abspath(os.path.join(current_dir, '.'))
msh_path = os.path.join(repo_root, 'micro_smart_hub')

if msh_path not in sys.path:
    sys.path.append(msh_path)

if repo_root not in sys.path:
    sys.path.append(repo_root)


import micro_registry.registry_rest_api
import micro_registry.component_rest_api
from micro_registry.registry import load_modules_from_directory
from micro_registry.component_loader import load_components_and_start_system

if __name__ == '__main__':
    registry_directory = os.path.join(os.path.abspath(os.path.dirname(os.path.dirname(__file__))), 'micro_smart_hub')
    load_modules_from_directory(registry_directory)
    load_modules_from_directory(os.path.dirname(__file__))
    # Load the components from the YAML file
    config_file_path = os.path.join(os.path.dirname(__file__), 'smart_hub_app.yaml')
    load_components_and_start_system(config_file_path)
