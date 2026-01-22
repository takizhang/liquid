import type { Status } from '../types';

interface StatusBadgeProps {
  status: Status;
  size?: 'sm' | 'md' | 'lg';
}

export const StatusBadge = ({ status, size = 'md' }: StatusBadgeProps) => {
  const sizeClasses = {
    sm: 'text-xl',
    md: 'text-2xl',
    lg: 'text-4xl',
  };

  const getGlowClass = () => {
    if (status.status === 'bullish' || status.status === 'slightly_bullish') {
      return 'drop-shadow-[0_0_8px_rgba(0,255,136,0.6)]';
    }
    if (status.status === 'bearish' || status.status === 'slightly_bearish') {
      return 'drop-shadow-[0_0_8px_rgba(255,51,102,0.6)]';
    }
    return 'drop-shadow-[0_0_8px_rgba(255,170,0,0.6)]';
  };

  return (
    <span
      className={`${sizeClasses[size]} ${getGlowClass()} transition-all duration-300`}
      title={status.status}
    >
      {status.emoji}
    </span>
  );
};
