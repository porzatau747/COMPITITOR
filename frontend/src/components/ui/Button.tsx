import React from 'react';
export function Button({ children, variant, size, ...props }: any) {
  return <button {...props}>{children}</button>;
}
