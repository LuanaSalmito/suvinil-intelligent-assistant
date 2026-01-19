import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { chatApi, paintsApi } from '../lib/api';
import { Button } from '../components/ui/Button';
import { ChatBubble, ChatBubbleMessage } from '../components/chat/ChatBubble';
import { ChatInput } from '../components/chat/ChatInput';
import { ChatMessageList } from '../components/chat/ChatMessageList';
import { Settings, LogOut, LayoutDashboard, LogIn, Paperclip, Image as ImageIcon } from 'lucide-react';

export function Chat() {
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [paintCount, setPaintCount] = useState(null);
  const { user, logout, isAdmin, isAuthenticated } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    let isMounted = true;
    const loadPaintCount = async () => {
      try {
        const data = await paintsApi.getCount();
        if (isMounted && typeof data?.total === 'number') {
          setPaintCount(data.total);
        }
      } catch (error) {
        console.error('Error loading paint count:', error);
      }
    };
    loadPaintCount();
    return () => {
      isMounted = false;
    };
  }, []);

  const handleSendMessage = async () => {
    if (!inputValue.trim() || isLoading) return;

    const userMessage = inputValue.trim();
    setInputValue('');
    setMessages((prev) => [...prev, { role: 'user', content: userMessage }]);

    setIsLoading(true);
    try {
      const response = await chatApi.sendMessage(userMessage, false);
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: response.response },
      ]);
    } catch (error) {
      console.error('Error sending message:', error);
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: 'Desculpe, ocorreu um erro. Tente novamente.',
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleResetChat = async () => {
    try {
      if (isAuthenticated) {
        await chatApi.resetChat();
      }
      setMessages([]);
    } catch (error) {
      console.error('Error resetting chat:', error);
      // Se falhar, apenas limpa as mensagens localmente
      setMessages([]);
    }
  };

  const handleLogout = () => {
    logout();
    setMessages([]); // Limpa as mensagens ao fazer logout
  };

  const handleLogin = () => {
    navigate('/login');
  };

  return (
    <div className="flex flex-col h-screen bg-background">
      {/* Header */}
      <header className="border-b bg-card px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h1 className="text-xl font-bold">Suvinil AI</h1>
          {user && (
            <span className="text-sm text-muted-foreground">
              {user.full_name || user.username || user.email}
            </span>
          )}
          {!user && (
            <span className="text-sm text-muted-foreground">Usuário Anônimo</span>
          )}
        </div>
        <div className="flex items-center gap-2">
          {isAuthenticated && isAdmin() && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => navigate('/admin')}
            >
              <LayoutDashboard className="h-4 w-4 mr-2" />
              Admin
            </Button>
          )}
          <Button variant="outline" size="sm" onClick={handleResetChat}>
            <Settings className="h-4 w-4 mr-2" />
            Limpar
          </Button>
          {isAuthenticated ? (
            <Button variant="outline" size="sm" onClick={handleLogout}>
              <LogOut className="h-4 w-4 mr-2" />
              Sair
            </Button>
          ) : (
            <Button variant="outline" size="sm" onClick={handleLogin}>
              <LogIn className="h-4 w-4 mr-2" />
              Entrar
            </Button>
          )}
        </div>
      </header>

      {/* Chat Messages */}
      <div className="flex-1 overflow-hidden">
        <ChatMessageList>
          {messages.length === 0 ? (
            <div className="flex items-center justify-center h-full">
              <div className="text-left max-w-xl space-y-3">
                <p className="text-lg font-semibold">
                  Oi! Me conta o que você quer pintar e o que precisa na tinta.
                </p>
                <p className="text-muted-foreground">
                  Posso sugerir opções do nosso catálogo ({paintCount ?? 5} disponíveis) com base no ambiente e no acabamento que você prefere.
                </p>
                <p className="text-muted-foreground">
                  Exemplo: "Quero pintar o quarto, algo fácil de limpar e sem cheiro forte."
                </p>
              </div>
            </div>
          ) : (
            messages.map((message, index) => (
              <ChatBubble key={index} variant={message.role === 'user' ? 'sent' : 'received'}>
                <ChatBubbleMessage variant={message.role === 'user' ? 'sent' : 'received'}>
                  <div className="text-sm whitespace-pre-wrap">{message.content}</div>
                </ChatBubbleMessage>
              </ChatBubble>
            ))
          )}
          {isLoading && (
            <ChatBubble variant="received">
              <ChatBubbleMessage variant="received" isLoading={true} />
            </ChatBubble>
          )}
        </ChatMessageList>
      </div>

      {/* Chat Input */}
      <div className="border-t bg-card p-4">
        <div className="flex gap-2 max-w-4xl mx-auto">
          <div className="flex-1 border rounded-lg overflow-hidden bg-background flex items-center gap-2">
            <button
              type="button"
              className="p-2 rounded-md hover:bg-accent text-muted-foreground hover:text-foreground transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex-shrink-0"
              title="Anexar foto (em breve)"
              disabled
            >
              <ImageIcon className="h-5 w-5" />
            </button>
            <div className="flex-1 min-w-0">
              <ChatInput
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onSubmit={handleSendMessage}
                placeholder="Digite sua mensagem..."
                disabled={isLoading}
                className="border-0 focus-visible:ring-0"
              />
            </div>
          </div>
          <Button onClick={handleSendMessage} disabled={isLoading || !inputValue.trim()}>
            Enviar
          </Button>
        </div>
      </div>
    </div>
  );
}