import { cn } from '../../lib/utils';

export function ChatBubble({ children, className, variant = 'received', ...props }) {
  return (
    <div
      className={cn(
        'flex items-start gap-3',
        variant === 'sent' ? 'flex-row-reverse' : 'flex-row',
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
}

export function ChatBubbleMessage({
  children,
  className,
  variant = 'received',
  isLoading = false,
  ...props
}) {
  return (
    <div
      className={cn(
        'max-w-[75%] rounded-lg p-3',
        variant === 'sent'
          ? 'bg-primary text-primary-foreground'
          : 'bg-muted text-foreground',
        className
      )}
      {...props}
    >
      {isLoading ? (
        <div className="space-y-2">
          <div className="text-sm text-muted-foreground italic">
            Pensando...
          </div>
          <div className="flex items-center space-x-2">
            <div className="h-2 w-2 rounded-full bg-current animate-pulse" />
            <div className="h-2 w-2 rounded-full bg-current animate-pulse delay-75" />
            <div className="h-2 w-2 rounded-full bg-current animate-pulse delay-150" />
          </div>
        </div>
      ) : (
        children
      )}
    </div>
  );
}