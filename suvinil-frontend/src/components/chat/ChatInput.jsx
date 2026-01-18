import { useRef, useEffect } from 'react';
import { cn } from '../../lib/utils';

export function ChatInput({ className, value, onSubmit, ...props }) {
  const textareaRef = useRef(null);

  const adjustHeight = () => {
    const textarea = textareaRef.current;
    if (!textarea) return;

    const maxHeight = 200;
    textarea.style.height = 'auto';
    const newHeight = Math.min(textarea.scrollHeight, maxHeight);
    textarea.style.height = `${newHeight}px`;
    textarea.style.overflowY = textarea.scrollHeight > maxHeight ? 'auto' : 'hidden';
  };

  useEffect(() => {
    adjustHeight();
  }, [value]);

  const handleInput = () => {
    adjustHeight();
  };

  const handleKeyDown = (event) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      onSubmit?.();
    }
  };

  return (
    <textarea
      ref={textareaRef}
      className={cn(
        'w-full resize-none text-base focus-visible:outline-none disabled:cursor-not-allowed disabled:opacity-50 min-h-12 rounded-lg bg-background border-0 p-3 shadow-none focus-visible:ring-0 break-words',
        className
      )}
      onInput={handleInput}
      onKeyDown={handleKeyDown}
      rows={1}
      value={value}
      {...props}
    />
  );
}