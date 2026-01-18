# 📊 Modelos Adicionais - Análise de Necessidade

## ✅ Modelo 1: ChatHistory/Message (RECOMENDADO se precisar persistência)

### Situação Atual
- Memória em RAM (`ConversationBufferMemory` + `_agent_sessions = {}`)
- Perdido ao reiniciar servidor
- Não funciona com múltiplos servidores

### Quando Criar
✅ **Criar se:**
- Precisa que conversas persistam após reinício
- Vai fazer deploy em produção
- Precisa histórico de conversas por usuário

❌ **Não criar se:**
- É apenas protótipo/local
- Não precisa persistir conversas
- Memória em RAM é suficiente

### Estrutura Sugerida (se criar):
```python
class ChatMessage(Base):
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    role = Column(String)  # 'user' ou 'assistant'
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
```

---

## ❌ Modelo 2: Embeddings no PostgreSQL (NÃO NECESSÁRIO)

### Situação Atual
- ✅ **ChromaDB já está sendo usado** (`./chroma_db/`)
- ✅ Funciona bem para embeddings
- ✅ Não precisa no PostgreSQL

### Decisão
**NÃO criar** - ChromaDB é suficiente e mais adequado para vetores.

---

## ⚠️ Modelo 3: AILogs (OPCIONAL - Nice to have)

### Situação Atual
- Não há logging estruturado de interações IA

### Quando Criar
✅ **Criar se:**
- Precisa debug de problemas de IA
- Quer métricas (tokens usados, custos)
- Precisa auditoria para produção

❌ **Não criar se:**
- É protótipo/MVP
- Logs simples (arquivo .log) são suficientes
- Não há necessidade de análise detalhada

### Estrutura Sugerida (se criar):
```python
class AILog(Base):
    __tablename__ = "ai_logs"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    user_query = Column(Text)
    ai_response = Column(Text)
    model_used = Column(String)
    prompt_tokens = Column(Integer)
    completion_tokens = Column(Integer)
    tools_called = Column(JSON)  # Lista de ferramentas usadas
    created_at = Column(DateTime, default=datetime.utcnow)
```

---

## 🎯 Recomendação Final

### Para o Desafio Loomi (MVP):

**Prioridade ALTA:**
1. **ChatHistory** - Se o requisito menciona "gerenciar contexto", provavelmente querem persistência

**Prioridade BAIXA:**
2. **AILogs** - Útil mas não essencial para MVP

**NÃO fazer:**
3. **Embeddings no PostgreSQL** - ChromaDB já resolve

### Fluxo de Trabalho

```bash
# Se decidir criar ChatHistory:
1. Criar modelo em app/models/chat_message.py
2. Criar migração: alembic revision --autogenerate -m "add chat messages"
3. Aplicar: alembic upgrade head
4. Modificar AgentService para salvar/carregar do banco
```
