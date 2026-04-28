'use client';
import { Box, BoxProps } from '@chakra-ui/react';

interface GlassCardProps extends BoxProps {
  children: React.ReactNode;
  accentColor?: string;
}

export function GlassCard({ children, accentColor, ...props }: GlassCardProps) {
  return (
    <Box
      bg="white"
      borderRadius="2xl"
      boxShadow="0 2px 16px rgba(99,102,241,0.07), 0 1px 4px rgba(0,0,0,0.05)"
      border="1px solid"
      borderColor="purple.50"
      p={6}
      position="relative"
      overflow="hidden"
      transition="all 0.2s"
      _hover={{
        boxShadow: '0 8px 30px rgba(99,102,241,0.13), 0 2px 8px rgba(0,0,0,0.07)',
        transform: 'translateY(-1px)',
      }}
      _before={{
        content: '""',
        position: 'absolute',
        top: 0,
        left: 0,
        right: 0,
        height: '3px',
        bgGradient: accentColor
          ? undefined
          : 'linear(to-r, brand.400, purple.400)',
        bg: accentColor ?? undefined,
        borderRadius: '2xl 2xl 0 0',
      }}
      {...props}
    >
      {children}
    </Box>
  );
}
