'use client';
import { Box, BoxProps } from '@chakra-ui/react';
import { motion } from 'framer-motion';
import React from 'react';

interface PageWrapperProps extends BoxProps {
  children: React.ReactNode;
}

export function PageWrapper({ children, ...props }: PageWrapperProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, ease: 'easeOut' }}
      style={{ width: '100%', display: 'flex', justifyContent: 'center' }}
    >
      <Box w="full" {...props}>
        {children}
      </Box>
    </motion.div>
  );
}
