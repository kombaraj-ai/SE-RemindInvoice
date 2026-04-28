'use client';
import { Box, Flex } from '@chakra-ui/react';
import { Sidebar } from './Sidebar';
import React from 'react';

interface AppShellProps {
  children: React.ReactNode;
}

export function AppShell({ children }: AppShellProps) {
  return (
    <Flex minH="100vh" bg="#f5f5fb">
      <Sidebar />
      <Box
        flex={1}
        overflowX="hidden"
        overflowY="auto"
        bgGradient="linear(135deg, #f5f5fb 0%, #ede9fe 40%, #f0fdf4 100%)"
        minH="100vh"
      >
        <Box maxW="1280px" mx="auto" px={8} py={8}>
          {children}
        </Box>
      </Box>
    </Flex>
  );
}
