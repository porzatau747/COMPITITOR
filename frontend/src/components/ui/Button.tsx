import type { ButtonHTMLAttributes, ReactNode } from 'react';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  children?: ReactNode;
  variant?: string;
  size?: string;
}

export function Button({ children, variant, size, ...props }: ButtonProps) {
  void variant;
  void size;
  return <button {...props}>{children}</button>;
}
