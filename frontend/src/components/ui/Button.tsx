import type { ButtonHTMLAttributes, ReactNode } from 'react';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  children: ReactNode;
  variant?: string;
  size?: string;
}

export function Button({ children, variant: _variant, size: _size, ...props }: ButtonProps) {
  const dataProps = { 'data-variant': _variant, 'data-size': _size };
  return <button {...dataProps} {...props}>{children}</button>;
}
