import { forwardRef } from 'react';
import clsx from 'clsx';

export const Button = forwardRef(function Button(
  { variant = 'primary', size = 'md', className, children, ...props },
  ref
) {
  return (
    <button
      ref={ref}
      className={clsx('ow-button', `ow-button-${variant}`, `ow-button-${size}`, className)}
      {...props}
    >
      {children}
    </button>
  );
});
