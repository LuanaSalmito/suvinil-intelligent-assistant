import { useRef, useEffect, useState } from 'react';
import { ArrowDown } from 'lucide-react';
import { Button } from '../ui/Button';

export function ChatMessageList({ children, className, smooth = false, ...props }) {
  const scrollRef = useRef(null);
  const [isAtBottom, setIsAtBottom] = useState(true);

  const checkScrollPosition = () => {
    if (!scrollRef.current) return;
    const { scrollTop, scrollHeight, clientHeight } = scrollRef.current;
    const threshold = 100;
    setIsAtBottom(scrollHeight - scrollTop - clientHeight < threshold);
  };

  const scrollToBottom = (behavior = 'smooth') => {
    if (scrollRef.current) {
      scrollRef.current.scrollTo({
        top: scrollRef.current.scrollHeight,
        behavior,
      });
    }
  };

  useEffect(() => {
    if (children) {
      setTimeout(() => scrollToBottom('auto'), 100);
    }
  }, [children]);

  useEffect(() => {
    const element = scrollRef.current;
    if (!element) return;

    element.addEventListener('scroll', checkScrollPosition);
    checkScrollPosition();

    return () => {
      element.removeEventListener('scroll', checkScrollPosition);
    };
  }, []);

  return (
    <div className="relative w-full h-full">
      <div
        ref={scrollRef}
        className={`flex flex-col w-full h-full p-4 overflow-y-auto ${className}`}
        style={{
          scrollBehavior: smooth ? 'smooth' : 'auto',
          WebkitOverflowScrolling: 'touch',
          overscrollBehavior: 'contain',
        }}
        onWheel={checkScrollPosition}
        onTouchMove={checkScrollPosition}
        {...props}
      >
        <div className="flex flex-col gap-6">{children}</div>
      </div>

      {!isAtBottom && (
        <Button
          onClick={() => scrollToBottom()}
          size="icon"
          variant="outline"
          className="absolute bottom-2 left-1/2 transform -translate-x-1/2 inline-flex rounded-full shadow-md z-10 hover:scale-110 transition-transform"
          aria-label="Scroll to bottom"
        >
          <ArrowDown className="h-4 w-4" />
        </Button>
      )}
    </div>
  );
}