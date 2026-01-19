# 🎯 Sistema de Slot Filling - Fluxo de Conversação

## 📋 O que foi implementado

### 1️⃣ Slots Obrigatórios
```python
REQUIRED_SLOTS = {
    "environment": "interno ou externo",
    "surface_type": "parede, madeira, metal, azulejo"
}
```

### 2️⃣ Slots Opcionais (melhoram a recomendação)
```python
OPTIONAL_SLOTS = {
    "color": "azul, verde, branco, amarelo...",
    "finish_type": "fosco, acetinado, brilhante",
    "room_type": "quarto, sala, banheiro, cozinha"
}
```

---

## 🔄 Fluxo Correto (ANTES vs DEPOIS)

### ❌ ANTES (Errado)
```
Usuário: "Quero pintar meu quarto"
↓
Bot consulta especialistas sem info suficiente
↓
Bot: "Recomendo Tinta X para None, acabamento fosco, protege ferrugem"
❌ None aparece, recomendação genérica errada
```

### ✅ DEPOIS (Correto)
```
Usuário: "Quero pintar meu quarto"
↓
Bot detecta: faltam [environment, surface_type]
↓
Bot: "É para ambiente interno ou externo?"
↓
Usuário: "Interno"
↓
Bot detecta: falta [surface_type]
↓
Bot: "Qual a superfície? (parede, madeira, metal, azulejo)"
↓
Usuário: "Parede"
↓
✅ TEM TUDO → Consulta especialistas
↓
Bot: "Recomendo Suvinil Toque de Seda para paredes, acabamento fosco, lavável. R$ 89.50"
✅ Resposta completa e precisa!
```

---

## 🧪 Exemplos de Conversação

### Exemplo 1: Usuário direto (já dá todas as infos)

**Conversa:**
```
👤 Usuário: "Quero tinta azul fosco para parede interna da sala"

✅ Bot detecta:
   - color: azul
   - finish_type: fosco
   - surface_type: parede
   - environment: interno
   - room_type: sala

🤖 Bot: "Consultei nossos especialistas. Recomendo a Suvinil Toque de Seda 
       para paredes, acabamento fosco, lavável, sem odor. R$ 89.50.
       Quer ver uma imagem de como ficaria?"
```

### Exemplo 2: Usuário gradual (conversa natural)

**Conversa:**
```
👤 Usuário: "Quero pintar meu quarto"
🤖 Bot: "É para ambiente interno ou externo?"

👤 Usuário: "Interno"
🤖 Bot: "Qual a superfície? (parede, madeira, metal, azulejo)"

👤 Usuário: "Parede de gesso"
🤖 Bot: "Consultei nossos especialistas. Recomendo a Suvinil Premium 
       para paredes, acabamento fosco, alta cobertura. R$ 95.00."

👤 Usuário: "Tem em azul?"
🤖 Bot: "Sim! Suvinil Premium Azul Serenidade para paredes, 
       acabamento fosco. R$ 95.00. Quer ver uma imagem?"

👤 Usuário: "Sim"
🤖 Bot: "Aqui está uma visualização de como ficaria azul no ambiente!"
       [Imagem gerada pelo DALL-E]
```

### Exemplo 3: Madeira (superfície especial)

**Conversa:**
```
👤 Usuário: "Preciso pintar uma porta de madeira"

✅ Bot detecta:
   - surface_type: madeira
   - Falta: environment

🤖 Bot: "É para ambiente interno ou externo?"

👤 Usuário: "Interno"

✅ TEM TUDO → Consulta especialista de durabilidade

🤖 Bot: "Consultei nossos especialistas. Recomendo a Suvinil Esmalte 
       para madeira, acabamento semi-brilhante, protege madeira, 
       resistente. R$ 78.90."
```

---

## 🛡️ Proteções Implementadas

### 1. Nunca mostrar `None` ao usuário
```python
# ANTES
f"para {context.get('surface_type')}"  # → "para None" ❌

# DEPOIS
surface = context.get('surface_type') or "paredes"
f"para {surface}"  # → "para paredes" ✅
```

### 2. Especialistas não "chutam"
```python
# Em cada especialista
if not context.get("environment"):
    return {
        "recommendations": [],
        "needs_more_info": True
    }
```

### 3. Validação antes de consultar
```python
if not self._has_required_slots():
    return self._generate_slot_question()
# Só consulta especialistas se tiver info mínima
```

### 4. Slots acumulam ao longo da conversa
```python
# Mensagem 1: "quarto"
accumulated_slots = {"room_type": "quarto", "environment": "interno"}

# Mensagem 2: "parede"
accumulated_slots = {"room_type": "quarto", "environment": "interno", "surface_type": "parede"}

# Usa contexto acumulado mesmo que não repita
```

---

## 📊 Metadados de Debug

A resposta agora inclui metadados úteis:

```json
{
  "response": "É para ambiente interno ou externo?",
  "metadata": {
    "mode": "slot_filling",
    "missing_slots": ["environment", "surface_type"],
    "accumulated_slots": {
      "color": "azul",
      "environment": null,
      "surface_type": null
    }
  }
}
```

---

## 🎨 Geração de Imagem (DALL-E)

A visualização agora usa contexto acumulado:

```
👤 "rosa para madeira vocês tem?"
🤖 "É interno ou externo?"
👤 "Interno"
🤖 "Recomendo Suvinil Semi-brilhante Rosa 19..."

👤 "pode me mostrar uma imagem?"
✅ Bot usa contexto armazenado:
   - color: rosa
   - finish: semi-brilhante
   - environment: interno

🤖 [Gera imagem com DALL-E]
    "Aqui está uma visualização de como ficaria rosa no ambiente!"
```

---

## 🔧 Arquivos Modificados

1. **orchestrator.py**
   - ✅ Sistema de slots obrigatórios
   - ✅ Validação antes de consultar
   - ✅ Acúmulo de contexto
   - ✅ Fallbacks para None

2. **specialists.py**
   - ✅ Validação de contexto mínimo
   - ✅ Retorno com `needs_more_info`
   - ✅ Não "chutar" sem dados

3. **ai_chat.py** (endpoint)
   - ✅ Metadados de debug
   - ✅ Suporte a slot_filling mode

---

## 🎯 Resultado Final

### O que estava errado:
- ❌ Bot recomendava sem informação suficiente
- ❌ Mostrava "None" ao usuário
- ❌ Inventava características (ferrugem, anti-mofo)
- ❌ Ordem errada: recomendar → perguntar

### O que foi corrigido:
- ✅ Bot pergunta ANTES de recomendar
- ✅ Valida slots obrigatórios
- ✅ Nunca mostra None
- ✅ Especialistas não "chutam"
- ✅ Ordem correta: perguntar → coletar → recomendar
- ✅ Contexto acumulado ao longo da conversa
- ✅ Respostas precisas e personalizadas

---

## 🚀 Como Testar

### Teste 1: Fluxo Gradual
```bash
POST /api/v1/ai/chat
{"message": "quero pintar meu quarto"}

# Deve perguntar ambiente e superfície

POST /api/v1/ai/chat
{"message": "interno, parede"}

# Deve recomendar produto específico
```

### Teste 2: Fluxo Direto
```bash
POST /api/v1/ai/chat
{"message": "tinta azul fosco para parede interna"}

# Deve recomendar direto (tem todas as infos)
```

### Teste 3: Visualização
```bash
POST /api/v1/ai/chat
{"message": "rosa para madeira"}

POST /api/v1/ai/chat
{"message": "interno"}

POST /api/v1/ai/chat
{"message": "pode me mostrar uma imagem?"}

# Deve gerar imagem com DALL-E
```

---

## 📝 Notas Técnicas

- Slots são resetados quando usuário chama `/chat/reset`
- Contexto persiste durante toda a sessão
- Especialistas retornam `needs_more_info: True` quando precisam de dados
- Orquestrador decide quando consultar baseado em slots completos
- Fallbacks garantem UX limpo mesmo com dados incompletos

---

**Status: ✅ IMPLEMENTADO E TESTADO**
