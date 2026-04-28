'use client';
import {
  Box,
  Heading,
  HStack,
  VStack,
  Text,
  Badge,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  TableContainer,
  Divider,
  Spinner,
  Center,
  Container,
} from '@chakra-ui/react';
import { useQuery } from '@tanstack/react-query';
import { FileText } from 'lucide-react';
import { invoicesService } from '@/services/invoices';
import type { InvoiceStatus } from '@/types/invoice';

function statusColorScheme(status: InvoiceStatus): string {
  switch (status) {
    case 'paid': return 'green';
    case 'overdue': return 'red';
    case 'sent': return 'blue';
    case 'viewed': return 'purple';
    case 'cancelled': return 'gray';
    default: return 'gray';
  }
}

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  });
}

function formatCurrency(amount: number, currency = 'INR'): string {
  return new Intl.NumberFormat('en-IN', { style: 'currency', currency }).format(amount);
}

function PublicInvoiceContent({ token }: { token: string }) {
  const { data: invoice, isLoading, isError } = useQuery({
    queryKey: ['public-invoice', token],
    queryFn: () => invoicesService.getPublic(token),
    retry: false,
  });

  if (isLoading) {
    return (
      <Center minH="60vh">
        <Spinner size="xl" color="brand.500" />
      </Center>
    );
  }

  if (isError || !invoice) {
    return (
      <Center minH="60vh">
        <VStack spacing={4} textAlign="center">
          <Box
            w={16}
            h={16}
            bg="gray.100"
            borderRadius="full"
            display="flex"
            alignItems="center"
            justifyContent="center"
          >
            <FileText size={28} color="#9CA3AF" />
          </Box>
          <Heading size="md" color="gray.600">Invoice Not Found</Heading>
          <Text color="gray.400" maxW="360px">
            This invoice link is invalid or has expired. Please contact the sender for a new link.
          </Text>
        </VStack>
      </Center>
    );
  }

  return (
    <Box bg="white" minH="100vh">
      {/* Header */}
      <Box bg="white" borderBottom="1px solid" borderColor="gray.100" py={4} px={6}>
        <Container maxW="800px">
          <HStack spacing={2}>
            <Box
              w={8}
              h={8}
              bgGradient="linear(to-br, brand.500, brand.600)"
              borderRadius="lg"
              display="flex"
              alignItems="center"
              justifyContent="center"
            >
              <FileText size={16} color="white" />
            </Box>
            <Text fontWeight="700" fontSize="lg" color="gray.800">
              RemindInvoice
            </Text>
          </HStack>
        </Container>
      </Box>

      <Container maxW="800px" py={10}>
        {/* Invoice header */}
        <HStack justify="space-between" mb={8} flexWrap="wrap" gap={4}>
          <Box>
            <Text fontSize="xs" color="gray.400" textTransform="uppercase" letterSpacing="wide" mb={1}>
              Invoice
            </Text>
            <Heading size="xl" color="gray.800">{invoice.invoice_number}</Heading>
          </Box>
          <Badge
            colorScheme={statusColorScheme(invoice.status)}
            borderRadius="full"
            px={4}
            py={2}
            fontSize="md"
            textTransform="capitalize"
            fontWeight="600"
          >
            {invoice.status}
          </Badge>
        </HStack>

        {/* Dates & client row */}
        <HStack justify="space-between" mb={8} flexWrap="wrap" gap={6} align="flex-start">
          {/* From / To */}
          <HStack spacing={12} align="flex-start">
            <Box>
              <Text fontSize="xs" color="gray.400" textTransform="uppercase" letterSpacing="wide" mb={2}>
                Bill To
              </Text>
              {invoice.client ? (
                <VStack align="flex-start" spacing={0}>
                  <Text fontWeight="600" color="gray.800">{invoice.client.name}</Text>
                  {invoice.client.company_name && (
                    <Text fontSize="sm" color="gray.500">{invoice.client.company_name}</Text>
                  )}
                  <Text fontSize="sm" color="gray.500">{invoice.client.email}</Text>
                </VStack>
              ) : (
                <Text fontSize="sm" color="gray.500">Client #{invoice.client_id}</Text>
              )}
            </Box>
          </HStack>

          {/* Dates */}
          <VStack align="flex-end" spacing={2}>
            <HStack spacing={6}>
              <Text fontSize="sm" color="gray.500">Issue Date</Text>
              <Text fontSize="sm" fontWeight="600" color="gray.800">{formatDate(invoice.issue_date)}</Text>
            </HStack>
            <HStack spacing={6}>
              <Text fontSize="sm" color="gray.500">Due Date</Text>
              <Text fontSize="sm" fontWeight="600" color={invoice.status === 'overdue' ? 'red.500' : 'gray.800'}>
                {formatDate(invoice.due_date)}
              </Text>
            </HStack>
            <HStack spacing={6}>
              <Text fontSize="sm" color="gray.500">Currency</Text>
              <Text fontSize="sm" fontWeight="600" color="gray.800">{invoice.currency}</Text>
            </HStack>
          </VStack>
        </HStack>

        <Divider mb={6} />

        {/* Line items */}
        <Box
          border="1px solid"
          borderColor="gray.100"
          borderRadius="xl"
          overflow="hidden"
          mb={6}
        >
          <TableContainer>
            <Table variant="simple">
              <Thead bg="gray.50">
                <Tr>
                  <Th fontSize="xs" textTransform="uppercase" color="gray.500" w="50%">Description</Th>
                  <Th fontSize="xs" textTransform="uppercase" color="gray.500" isNumeric>Qty</Th>
                  <Th fontSize="xs" textTransform="uppercase" color="gray.500" isNumeric>Unit Price</Th>
                  <Th fontSize="xs" textTransform="uppercase" color="gray.500" isNumeric>Amount</Th>
                </Tr>
              </Thead>
              <Tbody>
                {(invoice.items ?? []).map((item, idx) => (
                  <Tr key={item.id ?? idx}>
                    <Td>
                      <Text fontSize="sm" color="gray.700">{item.description}</Text>
                    </Td>
                    <Td isNumeric>
                      <Text fontSize="sm" color="gray.600">{item.quantity}</Text>
                    </Td>
                    <Td isNumeric>
                      <Text fontSize="sm" color="gray.600">
                        {formatCurrency(item.unit_price, invoice.currency)}
                      </Text>
                    </Td>
                    <Td isNumeric>
                      <Text fontSize="sm" fontWeight="600" color="gray.800">
                        {formatCurrency(item.amount, invoice.currency)}
                      </Text>
                    </Td>
                  </Tr>
                ))}
              </Tbody>
            </Table>
          </TableContainer>

          {/* Totals */}
          <Box px={6} py={4} bg="gray.50" borderTop="1px solid" borderColor="gray.100">
            <VStack align="flex-end" spacing={2}>
              <HStack justify="space-between" w="280px">
                <Text fontSize="sm" color="gray.500">Subtotal</Text>
                <Text fontSize="sm" color="gray.700">{formatCurrency(invoice.subtotal, invoice.currency)}</Text>
              </HStack>
              <HStack justify="space-between" w="280px">
                <Text fontSize="sm" color="gray.500">Tax ({invoice.tax_rate}%)</Text>
                <Text fontSize="sm" color="gray.700">{formatCurrency(invoice.tax_amount, invoice.currency)}</Text>
              </HStack>
              {invoice.discount_amount > 0 && (
                <HStack justify="space-between" w="280px">
                  <Text fontSize="sm" color="gray.500">Discount</Text>
                  <Text fontSize="sm" color="red.500">-{formatCurrency(invoice.discount_amount, invoice.currency)}</Text>
                </HStack>
              )}
              <Divider w="280px" />
              <HStack justify="space-between" w="280px">
                <Text fontSize="lg" fontWeight="700" color="gray.800">Total</Text>
                <Text fontSize="lg" fontWeight="700" color="#4F46E5">
                  {formatCurrency(invoice.total, invoice.currency)}
                </Text>
              </HStack>
            </VStack>
          </Box>
        </Box>

        {/* Notes */}
        {invoice.notes && (
          <Box
            border="1px solid"
            borderColor="gray.100"
            borderRadius="xl"
            p={5}
            mb={6}
          >
            <Text fontSize="xs" color="gray.400" textTransform="uppercase" letterSpacing="wide" mb={2}>
              Notes
            </Text>
            <Text fontSize="sm" color="gray.600" whiteSpace="pre-wrap">{invoice.notes}</Text>
          </Box>
        )}

        {/* Footer */}
        <Box textAlign="center" py={6}>
          <Text fontSize="xs" color="gray.400">
            Powered by{' '}
            <Text as="span" fontWeight="600" color="#4F46E5">
              RemindInvoice
            </Text>
          </Text>
        </Box>
      </Container>
    </Box>
  );
}

export default function PublicInvoicePage({ params }: { params: { token: string } }) {
  return <PublicInvoiceContent token={params.token} />;
}
