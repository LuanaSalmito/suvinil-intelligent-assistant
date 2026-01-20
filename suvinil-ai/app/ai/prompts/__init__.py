"""
Sistema de gerenciamento de prompts versionados.

Todos os prompts usados no sistema são carregados de arquivos YAML
para facilitar versionamento, experimentação e manutenção.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any

# Diretório onde os prompts estão armazenados
PROMPTS_DIR = Path(__file__).parent


def load_prompt_file(filename: str) -> Dict[str, Any]:
    """
    Carrega um arquivo YAML de prompts.
    
    Args:
        filename: Nome do arquivo (com ou sem extensão .yaml)
    
    Returns:
        Dicionário com os prompts carregados
    """
    if not filename.endswith('.yaml'):
        filename = f"{filename}.yaml"
    
    filepath = PROMPTS_DIR / filename
    
    if not filepath.exists():
        raise FileNotFoundError(f"Arquivo de prompts não encontrado: {filepath}")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


class PromptManager:
    """
    Gerenciador centralizado de prompts.
    Carrega todos os prompts na inicialização para performance.
    """
    
    def __init__(self):
        self._prompts = {}
        self._load_all_prompts()
    
    def _load_all_prompts(self):
        """Carrega todos os arquivos de prompts disponíveis."""
        try:
            self._prompts['orchestrator'] = load_prompt_file('orchestrator_prompts.yaml')
        except FileNotFoundError:
            self._prompts['orchestrator'] = {}
        
        try:
            self._prompts['specialists'] = load_prompt_file('specialist_prompts.yaml')
        except FileNotFoundError:
            self._prompts['specialists'] = {}
        
        try:
            self._prompts['image'] = load_prompt_file('image_prompts.yaml')
        except FileNotFoundError:
            self._prompts['image'] = {}
    
    def get_orchestrator_prompts(self) -> Dict[str, Any]:
        """Retorna todos os prompts do orquestrador."""
        return self._prompts.get('orchestrator', {})
    
    def get_specialist_prompts(self) -> Dict[str, Any]:
        """Retorna todos os prompts dos especialistas."""
        return self._prompts.get('specialists', {})
    
    def get_image_prompts(self) -> Dict[str, Any]:
        """Retorna todos os prompts de geração de imagem."""
        return self._prompts.get('image', {})
    
    def reload(self):
        """Recarrega todos os prompts (útil para testes/desenvolvimento)."""
        self._prompts = {}
        self._load_all_prompts()


# Instância global para uso em todo o sistema
prompt_manager = PromptManager()
