'use client';
import {
  Box,
  Heading,
  Text,
  SimpleGrid,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  Flex,
  Spinner,
  Badge,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  TableContainer,
  HStack,
  Button,
} from '@chakra-ui/react';
import { IndianRupee, AlertCircle, CheckCircle, Users } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { useRouter } from 'next/navigation';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { AppShell } from '@/components/layout/AppShell';
import { PageWrapper } from '@/components/layout/PageWrapper';
import { dashboardService } from '@/services/dashboard';
import type { InvoiceStatus } from '@/types/invoice';

function formatCurrency(amount: number): string {
  return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(amount);
}

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString('en-IN', { year: 'numeric', month: 'short', day: 'numeric' });
}

function statusColorScheme(status: InvoiceStatus): string {
  switch (status) {
    case 'paid': return 'green';
    case 'overdue': return 'red';
    case 'sent': return 'blue';
    case 'viewed': return 'purple';
    case 'cancelled': return 'gray';
    default: return 'yellow';
  }
}

interface StatCardProps {
  label: string;
  value: string;
  helpText: string;
  icon: React.ReactNode;
  iconBg: string;
  valueColor: string;
  accentGradient: string;
  isLoading?: boolean;
}

function StatCard({ label, value, helpText, icon, iconBg, valueColor, accentGradient, isLoading }: StatCardProps) {
  return (
    <Box
      bg="white"
      borderRadius="2xl"
      p={6}
      position="relative"
      overflow="hidden"
      boxShadow="0 2px 16px rgba(0,0,0,0.06)"
      border="1px solid"
      borderColor="gray.100"
      transition="all 0.2s"
      _hover={{ transform: 'translateY(-2px)', boxShadow: '0 8px 28px rgba(0,0,0,0.1)' }}
      _before={{
        content: '""',
        position: 'absolute',
        top: 0, left: 0, right: 0,
        height: '4px',
        bgGradient: accentGradient,
      }}
    >
      <Flex justify="space-between" align="flex-start">
        <Stat>
          <StatLabel color="gray.500" fontSize="xs" textTransform="uppercase" letterSpacing="wider" fontWeight="600" mb={2}>
            {label}
          </StatLabel>
          <StatNumber fontSize="2xl" fontWeight="700" color={valueColor} mb={1}>
            {isLoading ? <Spinner size="sm" color={valueColor} /> : value}
          </StatNumber>
          <StatHelpText color="gray.400" fontSize="xs" mb={0}>{helpText}</StatHelpText>
        </Stat>
        <Flex w="44px" h="44px" borderRadius="xl" bg={iconBg} align="center" justify="center" flexShrink={0}>
          {icon}
        </Flex>
      </Flex>
    </Box>
  );
}

function DashboardContent() {
  const router = useRouter();

  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: () => dashboardService.getStats(),
  });

  const { data: recent, isLoading: recentLoading } = useQuery({
    queryKey: ['dashboard-recent'],
    queryFn: () => dashboardService.getRecentInvoices(),
  });

  return (
    <PageWrapper>
      <Box mb={8}>
        <Heading size="lg" mb={1} bgGradient="linear(to-r, brand.600, purple.500)" bgClip="text" fontWeight="800">
          Dashboard
        </Heading>
        <Text color="gray.500" fontSize="sm">Welcome back. Here&apos;s an overview of your invoices.</Text>
      </Box>

      <SimpleGrid columns={{ base: 1, sm: 2, lg: 4 }} spacing={5} mb={8}>
        <StatCard
          label="Total Outstanding"
          value={stats ? formatCurrency(stats.outstanding) : '₹0'}
          helpText="Across all invoices"
          icon={<IndianRupee size={20} color="#6366f1" />}
          iconBg="rgba(99,102,241,0.1)"
          valueColor="brand.600"
          accentGradient="linear(to-r, brand.400, brand.600)"
          isLoading={statsLoading}
        />
        <StatCard
          label="Overdue"
          value={stats ? `${stats.overdue_count} invoice${stats.overdue_count !== 1 ? 's' : ''}` : '0'}
          helpText="Past due date"
          icon={<AlertCircle size={20} color="#f43f5e" />}
          iconBg="rgba(244,63,94,0.1)"
          valueColor="red.500"
          accentGradient="linear(to-r, red.400, pink.400)"
          isLoading={statsLoading}
        />
        <StatCard
          label="Paid This Month"
          value={stats ? formatCurrency(stats.total_paid) : '₹0'}
          helpText="Current month"
          icon={<CheckCircle size={20} color="#10b981" />}
          iconBg="rgba(16,185,129,0.1)"
          valueColor="green.500"
          accentGradient="linear(to-r, green.400, teal.400)"
          isLoading={statsLoading}
        />
        <StatCard
          label="Active Clients"
          value={stats ? String(stats.total_clients) : '0'}
          helpText="Total clients"
          icon={<Users size={20} color="#8b5cf6" />}
          iconBg="rgba(139,92,246,0.1)"
          valueColor="purple.600"
          accentGradient="linear(to-r, purple.400, pink.400)"
          isLoading={statsLoading}
        />
      </SimpleGrid>

      <Box bg="white" borderRadius="2xl" boxShadow="0 2px 16px rgba(0,0,0,0.06)" border="1px solid" borderColor="gray.100" overflow="hidden">
        <HStack justify="space-between" px={6} py={4} borderBottom="1px solid" borderColor="gray.100">
          <Heading size="sm" color="gray.700" fontWeight="700">Recent Invoices</Heading>
          <Button size="xs" variant="ghost" colorScheme="brand" onClick={() => router.push('/invoices')}>
            View all
          </Button>
        </HStack>

        {recentLoading ? (
          <Flex align="center" justify="center" py={12}>
            <Spinner size="lg" color="brand.500" />
          </Flex>
        ) : !recent?.items?.length ? (
          <Flex direction="column" align="center" justify="center" py={12} color="gray.400">
            <Box mb={3} opacity={0.4}><IndianRupee size={40} /></Box>
            <Text fontSize="sm" fontWeight="500" color="gray.400">No invoices yet. Create your first invoice to get started.</Text>
          </Flex>
        ) : (
          <TableContainer>
            <Table variant="simple" size="sm">
              <Thead bg="gray.50">
                <Tr>
                  <Th fontSize="xs" color="gray.500" textTransform="uppercase">Invoice #</Th>
                  <Th fontSize="xs" color="gray.500" textTransform="uppercase">Client</Th>
                  <Th fontSize="xs" color="gray.500" textTransform="uppercase">Due Date</Th>
                  <Th fontSize="xs" color="gray.500" textTransform="uppercase">Status</Th>
                  <Th fontSize="xs" color="gray.500" textTransform="uppercase" isNumeric>Amount</Th>
                </Tr>
              </Thead>
              <Tbody>
                {recent.items.map((inv) => (
                  <Tr
                    key={inv.id}
                    cursor="pointer"
                    _hover={{ bg: 'gray.50' }}
                    onClick={() => router.push(`/invoices/${inv.id}`)}
                  >
                    <Td>
                      <Text fontSize="sm" fontWeight="600" color="brand.500">{inv.invoice_number}</Text>
                    </Td>
                    <Td>
                      <Text fontSize="sm" color="gray.700">{inv.client?.name ?? `Client #${inv.client_id}`}</Text>
                      {inv.client?.company_name && (
                        <Text fontSize="xs" color="gray.400">{inv.client.company_name}</Text>
                      )}
                    </Td>
                    <Td>
                      <Text fontSize="sm" color="gray.600">{formatDate(inv.due_date)}</Text>
                    </Td>
                    <Td>
                      <Badge
                        colorScheme={statusColorScheme(inv.status)}
                        borderRadius="full"
                        px={2}
                        fontSize="xs"
                        textTransform="capitalize"
                      >
                        {inv.status}
                      </Badge>
                    </Td>
                    <Td isNumeric>
                      <Text fontSize="sm" fontWeight="600" color="gray.800">{formatCurrency(inv.total)}</Text>
                    </Td>
                  </Tr>
                ))}
              </Tbody>
            </Table>
          </TableContainer>
        )}
      </Box>
    </PageWrapper>
  );
}

export default function DashboardPage() {
  return (
    <ProtectedRoute>
      <AppShell>
        <DashboardContent />
      </AppShell>
    </ProtectedRoute>
  );
}
