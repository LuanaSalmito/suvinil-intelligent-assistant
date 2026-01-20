# Sistema de Prompts Versionados

Este diretório contém todos os prompts usados no sistema de IA do assistente Suvinil, organizados em arquivos YAML para facilitar o versionamento, experimentação e manutenção.

## Estrutura de Arquivos

### `orchestrator_prompts.yaml`
Contém todos os prompts usados pelo **OrchestratorAgent** (agente principal):

- **`style_guide`**: Guia de estilo para respostas do consultor técnico
- **`context_extraction`**: Prompt para extrair contexto (slots) da conversa do usuário
- **`final_synthesis`**: Prompt principal para gerar a resposta final ao usuário
- **`missing_slot_questions`**: Perguntas para solicitar informações faltantes
- **`no_product_responses`**: Respostas quando não há produto no catálogo
- **`no_catalog`**: Mensagem quando não há tintas cadastradas
- **`catalog_header`**: Cabeçalho para listagem de catálogo

### `specialist_prompts.yaml`
Contém prompts e base de conhecimento usados pelos **Specialists** (especialistas técnicos):

- **`color_insights`**: Insights sobre harmonização e efeitos de cada cor
- **`surface_expert`**: Mensagens do especialista em superfícies
- **`exterior_expert`**: Mensagens do especialista em ambientes externos
- **`interior_expert`**: Mensagens do especialista em ambientes internos
- **`color_expert`**: Mensagens do especialista em cores

### `image_prompts.yaml`
Contém configurações e prompts para geração de imagens com DALL-E:

- **`color_descriptions`**: Descrições de cores em inglês para o DALL-E
- **`finish_descriptions`**: Descrições de acabamentos para o DALL-E
- **`environment_map`**: Mapeamento de ambientes (português → inglês)
- **`dalle_prompt_template`**: Template principal do prompt DALL-E

## Como Usar

### Carregar Prompts no Código

```python
from app.ai.prompts import prompt_manager

# Carregar prompts do orquestrador
orchestrator_prompts = prompt_manager.get_orchestrator_prompts()
style_guide = orchestrator_prompts.get('style_guide')

# Carregar prompts dos especialistas
specialist_prompts = prompt_manager.get_specialist_prompts()
color_insights = specialist_prompts.get('color_insights')

# Carregar prompts de imagem
image_prompts = prompt_manager.get_image_prompts()
color_descriptions = image_prompts.get('color_descriptions')
```

### Recarregar Prompts (útil para desenvolvimento)

```python
from app.ai.prompts import prompt_manager

# Recarregar todos os prompts
prompt_manager.reload()
```

## Vantagens deste Approach

### 1. **Versionamento**
- Todos os prompts estão em arquivos de texto que podem ser versionados com git
- Histórico completo de mudanças nos prompts
- Fácil fazer rollback de prompts que não funcionaram bem

### 2. **Experimentação**
- Testar variações de prompts sem modificar código Python
- A/B testing de diferentes versões
- Facilita ajustes finos sem need de redeploy

### 3. **Colaboração**
- Product managers e designers podem revisar/sugerir prompts
- Documentação clara de cada prompt e seu propósito
- Separação clara entre lógica de negócio e conteúdo

### 4. **Manutenção**
- Mudanças de tom ou estilo centralizadas
- Fácil encontrar e atualizar prompts específicos
- Reduz duplicação de prompts similares

## Boas Práticas

### Ao Modificar Prompts:

1. **Teste localmente primeiro**: Sempre teste mudanças em ambiente de desenvolvimento
2. **Documente o motivo**: Use commits descritivos ao modificar prompts
3. **Preserve templates**: Mantenha placeholders como `{color}`, `{product_name}` etc.
4. **Consistência de tom**: Mantenha o tom profissional e consultivo

### Ao Adicionar Novos Prompts:

1. **Escolha o arquivo correto**:
   - Orquestrador → `orchestrator_prompts.yaml`
   - Especialistas → `specialist_prompts.yaml`
   - Imagens → `image_prompts.yaml`

2. **Use nomes descritivos**: Nomes de chaves devem ser claros e autoexplicativos

3. **Documente com comentários**: Use comentários YAML (`#`) para explicar prompts complexos

4. **Siga o padrão existente**: Mantenha consistência com prompts similares

## Exemplo de Modificação

```yaml
# Antes
color_insights:
  azul: "Tons de azul estimulam o foco."

# Depois (melhorado)
color_insights:
  azul: "Tons de azul estimulam o foco e a criatividade, sendo excelentes para escritórios modernos ou fachadas serenas."
```

## Troubleshooting

### Erro: "Arquivo de prompts não encontrado"
- Verifique se os arquivos YAML estão no diretório correto
- Certifique-se de que os nomes dos arquivos estão corretos

### Prompts não estão atualizando
- Em desenvolvimento, use `prompt_manager.reload()`
- Em produção, faça restart da aplicação após mudanças

### Erro de formatação YAML
- Valide o YAML em: https://www.yamllint.com/
- Verifique indentação (use 2 espaços)
- Strings multiline devem usar `|` ou `>`

## Roadmap Futuro

- [ ] Adicionar versionamento de prompts (v1, v2, etc.)
- [ ] Implementar A/B testing de prompts
- [ ] Adicionar métricas de performance por prompt
- [ ] Interface web para edição de prompts
- [ ] Suporte a múltiplos idiomas
