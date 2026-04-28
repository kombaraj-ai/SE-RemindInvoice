'use client';
import { Box, Stat, StatLabel, StatNumber, StatHelpText, StatArrow } from '@chakra-ui/react';

interface Props {
  label: string;
  value: string;
  helpText?: string;
  trend?: 'increase' | 'decrease';
  color?: string;
}

export function StatsCard({ label, value, helpText, trend, color }: Props) {
  return (
    <Box
      p={6}
      bg="white"
      rounded="xl"
      shadow="sm"
      borderLeft="4px solid"
      borderColor={color || 'brand.500'}
      transition="box-shadow 0.2s"
      _hover={{ shadow: 'md' }}
    >
      <Stat>
        <StatLabel color="gray.600" fontSize="xs" textTransform="uppercase" letterSpacing="wide">
          {label}
        </StatLabel>
        <StatNumber fontSize="2xl" fontWeight="bold" color="gray.800" mt={1}>
          {value}
        </StatNumber>
        {helpText && (
          <StatHelpText color="gray.500" fontSize="xs" mt={1}>
            {trend && <StatArrow type={trend} />}
            {helpText}
          </StatHelpText>
        )}
      </Stat>
    </Box>
  );
}
