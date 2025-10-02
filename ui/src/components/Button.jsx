import { forwardRef } from 'react';
import clsx from 'clsx';

export const Button = forwardRef(function Button(
  { as: Component = 'button', variant = 'primary', size = 'md', className, children, ...props },
  ref
) {
  return (
    <Component
      ref={ref}
      className={clsx('ow-button', `ow-button-${variant}`, `ow-button-${size}`, className)}
      {...props}
    >
      {children}
    </Component>
  );
});
