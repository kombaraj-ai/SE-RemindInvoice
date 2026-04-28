'use client';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import { Box, Heading } from '@chakra-ui/react';
import type { RevenueDataPoint } from '@/services/dashboard';

interface Props {
  data: RevenueDataPoint[];
}

export function RevenueChart({ data }: Props) {
  return (
    <Box bg="white" p={6} rounded="xl" shadow="sm" border="1px solid" borderColor="gray.100">
      <Heading size="sm" mb={4} color="gray.700">
        Revenue (Last 12 Months)
      </Heading>
      <ResponsiveContainer width="100%" height={250}>
        <BarChart data={data} margin={{ top: 4, right: 8, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis
            dataKey="month"
            tick={{ fontSize: 12, fill: '#718096' }}
            axisLine={false}
            tickLine={false}
          />
          <YAxis
            tick={{ fontSize: 12, fill: '#718096' }}
            axisLine={false}
            tickLine={false}
            tickFormatter={(v: number) => `$${v}`}
          />
          <Tooltip
            formatter={(value: number) => [`₹${value.toFixed(2)}`, 'Revenue']}
            contentStyle={{
              borderRadius: '8px',
              border: '1px solid #E2E8F0',
              boxShadow: '0 4px 12px rgba(0,0,0,0.08)',
            }}
          />
          <Bar dataKey="revenue" fill="#4F46E5" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </Box>
  );
}
