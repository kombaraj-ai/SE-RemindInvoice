'use client';
import { Button, ButtonProps } from '@chakra-ui/react';

interface GradientButtonProps extends ButtonProps {
  children: React.ReactNode;
}

export function GradientButton({ children, ...props }: GradientButtonProps) {
  return (
    <Button
      bgGradient="linear(to-r, brand.500, purple.500)"
      color="white"
      fontWeight="600"
      borderRadius="xl"
      boxShadow="0 4px 14px rgba(99,102,241,0.35)"
      _hover={{
        bgGradient: 'linear(to-r, brand.600, purple.600)',
        transform: 'translateY(-1px)',
        boxShadow: '0 6px 20px rgba(99,102,241,0.45)',
      }}
      _active={{
        bgGradient: 'linear(to-r, brand.700, purple.700)',
        transform: 'translateY(0)',
        boxShadow: '0 2px 8px rgba(99,102,241,0.3)',
      }}
      transition="all 0.2s"
      {...props}
    >
      {children}
    </Button>
  );
}
