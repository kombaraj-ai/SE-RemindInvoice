'use client';
import {
  Box,
  Button,
  HStack,
  Heading,
  Text,
  Badge,
  VStack,
  SimpleGrid,
  Stat,
  StatLabel,
  StatNumber,
  Spinner,
  Center,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  TableContainer,
  useToast,
  useDisclosure,
  AlertDialog,
  AlertDialogBody,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogContent,
  AlertDialogOverlay,
  Divider,
} from '@chakra-ui/react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useRouter } from 'next/navigation';
import { useRef } from 'react';
import { ArrowLeft, Edit, Trash2, FileText, User, Building2, Mail, Phone, MapPin } from 'lucide-react';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { AppShell } from '@/components/layout/AppShell';
import { GlassCard } from '@/components/ui/GlassCard';
import { GradientButton } from '@/components/ui/GradientButton';
import { PageWrapper } from '@/components/layout/PageWrapper';
import { clientsService } from '@/services/clients';
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
    month: 'short',
    day: 'numeric',
  });
}

function formatCurrency(amount: number, currency = 'INR'): string {
  return new Intl.NumberFormat('en-IN', { style: 'currency', currency }).format(amount);
}

function ClientDetailContent({ id }: { id: number }) {
  const router = useRouter();
  const toast = useToast();
  const queryClient = useQueryClient();
  const { isOpen, onOpen, onClose } = useDisclosure();
  const cancelRef = useRef<HTMLButtonElement>(null);

  const { data: client, isLoading, isError } = useQuery({
    queryKey: ['client', id],
    queryFn: () => clientsService.get(id),
  });

  const { data: invoicesData, isLoading: invoicesLoading } = useQuery({
    queryKey: ['client-invoices', id],
    queryFn: () => clientsService.getInvoices(id),
    enabled: !!id,
  });

  const deleteMutation = useMutation({
    mutationFn: () => clientsService.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['clients'] });
      toast({
        title: 'Client deleted',
        description: `${client?.name} has been removed.`,
        status: 'success',
        duration: 3000,
        isClosable: true,
      });
      router.push('/clients');
    },
    onError: () => {
      toast({
        title: 'Delete failed',
        description: 'Cannot delete a client with active invoices.',
        status: 'error',
        duration: 4000,
        isClosable: true,
      });
      onClose();
    },
  });

  if (isLoading) {
    return (
      <Center py={20}>
        <Spinner size="xl" color="brand.500" />
      </Center>
    );
  }

  if (isError || !client) {
    return (
      <Center py={20}>
        <VStack spacing={3}>
          <Text color="red.500" fontWeight="600">Client not found</Text>
          <Button variant="ghost" onClick={() => router.push('/clients')}>
            Back to Clients
          </Button>
        </VStack>
      </Center>
    );
  }

  const invoices = invoicesData?.items ?? [];

  return (
    <PageWrapper>
      {/* Header */}
      <HStack justify="space-between" mb={8} flexWrap="wrap" gap={3}>
        <HStack spacing={3}>
          <Button
            leftIcon={<ArrowLeft size={16} />}
            variant="ghost"
            size="sm"
            onClick={() => router.push('/clients')}
            color="gray.600"
          >
            Clients
          </Button>
          <User size={24} color="#4F46E5" />
          <Heading size="lg" color="gray.800">
            {client.name}
          </Heading>
          <Badge
            colorScheme={client.is_active ? 'green' : 'gray'}
            borderRadius="full"
            px={3}
            fontSize="sm"
          >
            {client.is_active ? 'Active' : 'Inactive'}
          </Badge>
        </HStack>
        <HStack spacing={2}>
          <Button
            leftIcon={<Edit size={16} />}
            variant="outline"
            colorScheme="brand"
            onClick={() => router.push(`/clients/${id}/edit`)}
          >
            Edit
          </Button>
          <Button
            leftIcon={<Trash2 size={16} />}
            colorScheme="red"
            variant="outline"
            onClick={onOpen}
          >
            Delete
          </Button>
        </HStack>
      </HStack>

      {/* Stats */}
      <SimpleGrid columns={{ base: 2, md: 4 }} spacing={4} mb={6}>
        <GlassCard>
          <Stat>
            <StatLabel color="gray.500" fontSize="xs" textTransform="uppercase" letterSpacing="wide">
              Total Invoiced
            </StatLabel>
            <StatNumber fontSize="xl" color="gray.800">
              {formatCurrency(client.total_invoiced ?? 0, client.currency)}
            </StatNumber>
          </Stat>
        </GlassCard>
        <GlassCard>
          <Stat>
            <StatLabel color="gray.500" fontSize="xs" textTransform="uppercase" letterSpacing="wide">
              Total Paid
            </StatLabel>
            <StatNumber fontSize="xl" color="green.500">
              {formatCurrency(client.total_paid ?? 0, client.currency)}
            </StatNumber>
          </Stat>
        </GlassCard>
        <GlassCard>
          <Stat>
            <StatLabel color="gray.500" fontSize="xs" textTransform="uppercase" letterSpacing="wide">
              Outstanding
            </StatLabel>
            <StatNumber fontSize="xl" color="orange.500">
              {formatCurrency(client.outstanding ?? 0, client.currency)}
            </StatNumber>
          </Stat>
        </GlassCard>
        <GlassCard>
          <Stat>
            <StatLabel color="gray.500" fontSize="xs" textTransform="uppercase" letterSpacing="wide">
              Invoices
            </StatLabel>
            <StatNumber fontSize="xl" color="gray.800">
              {client.invoice_count ?? 0}
            </StatNumber>
          </Stat>
        </GlassCard>
      </SimpleGrid>

      {/* Client Info */}
      <SimpleGrid columns={{ base: 1, md: 2 }} spacing={6} mb={6}>
        <GlassCard>
          <Heading size="sm" color="gray.700" mb={4}>
            Contact Information
          </Heading>
          <VStack align="stretch" spacing={3}>
            <HStack spacing={3}>
              <Mail size={16} color="#6B7280" />
              <Text fontSize="sm" color="gray.700">{client.email}</Text>
            </HStack>
            {client.phone && (
              <HStack spacing={3}>
                <Phone size={16} color="#6B7280" />
                <Text fontSize="sm" color="gray.700">{client.phone}</Text>
              </HStack>
            )}
            {client.company_name && (
              <HStack spacing={3}>
                <Building2 size={16} color="#6B7280" />
                <Text fontSize="sm" color="gray.700">{client.company_name}</Text>
              </HStack>
            )}
            {(client.address_line1 || client.city) && (
              <HStack spacing={3} align="flex-start">
                <Box mt="2px"><MapPin size={16} color="#6B7280" /></Box>
                <VStack align="flex-start" spacing={0}>
                  {client.address_line1 && (
                    <Text fontSize="sm" color="gray.700">{client.address_line1}</Text>
                  )}
                  {client.address_line2 && (
                    <Text fontSize="sm" color="gray.700">{client.address_line2}</Text>
                  )}
                  {(client.city || client.state || client.postal_code) && (
                    <Text fontSize="sm" color="gray.700">
                      {[client.city, client.state, client.postal_code].filter(Boolean).join(', ')}
                    </Text>
                  )}
                  {client.country && (
                    <Text fontSize="sm" color="gray.700">{client.country}</Text>
                  )}
                </VStack>
              </HStack>
            )}
          </VStack>
        </GlassCard>

        <GlassCard>
          <Heading size="sm" color="gray.700" mb={4}>
            Billing Details
          </Heading>
          <VStack align="stretch" spacing={3}>
            <HStack justify="space-between">
              <Text fontSize="sm" color="gray.500">Currency</Text>
              <Text fontSize="sm" fontWeight="600" color="gray.800">{client.currency}</Text>
            </HStack>
            <Divider />
            <HStack justify="space-between">
              <Text fontSize="sm" color="gray.500">Payment Terms</Text>
              <Text fontSize="sm" fontWeight="600" color="gray.800">
                Net {client.payment_terms_days} days
              </Text>
            </HStack>
            <Divider />
            <HStack justify="space-between">
              <Text fontSize="sm" color="gray.500">Member Since</Text>
              <Text fontSize="sm" fontWeight="600" color="gray.800">
                {formatDate(client.created_at)}
              </Text>
            </HStack>
            {client.notes && (
              <>
                <Divider />
                <Box>
                  <Text fontSize="xs" color="gray.500" mb={1} textTransform="uppercase" letterSpacing="wide">
                    Notes
                  </Text>
                  <Text fontSize="sm" color="gray.700">{client.notes}</Text>
                </Box>
              </>
            )}
          </VStack>
        </GlassCard>
      </SimpleGrid>

      {/* Invoices Table */}
      <GlassCard p={0} overflow="hidden">
        <Box px={6} py={4} borderBottom="1px solid" borderColor="gray.100">
          <HStack justify="space-between">
            <HStack spacing={2}>
              <FileText size={18} color="#4F46E5" />
              <Heading size="sm" color="gray.700">Invoices</Heading>
            </HStack>
            <GradientButton
              size="sm"
              leftIcon={<FileText size={14} />}
              onClick={() => router.push('/invoices/new')}
            >
              New Invoice
            </GradientButton>
          </HStack>
        </Box>

        {invoicesLoading ? (
          <Center py={10}>
            <Spinner size="lg" color="brand.500" />
          </Center>
        ) : invoices.length === 0 ? (
          <Center py={10}>
            <Text color="gray.400" fontSize="sm">No invoices for this client yet.</Text>
          </Center>
        ) : (
          <TableContainer>
            <Table variant="simple">
              <Thead bg="gray.50">
                <Tr>
                  <Th fontSize="xs" textTransform="uppercase" color="gray.500">Invoice #</Th>
                  <Th fontSize="xs" textTransform="uppercase" color="gray.500">Issue Date</Th>
                  <Th fontSize="xs" textTransform="uppercase" color="gray.500">Due Date</Th>
                  <Th fontSize="xs" textTransform="uppercase" color="gray.500" isNumeric>Amount</Th>
                  <Th fontSize="xs" textTransform="uppercase" color="gray.500">Status</Th>
                </Tr>
              </Thead>
              <Tbody>
                {invoices.map((invoice) => (
                  <Tr
                    key={invoice.id}
                    cursor="pointer"
                    _hover={{ bg: 'brand.50' }}
                    transition="background 0.15s"
                    onClick={() => router.push(`/invoices/${invoice.id}`)}
                  >
                    <Td>
                      <Text fontSize="sm" fontWeight="600" color="brand.500">
                        {invoice.invoice_number}
                      </Text>
                    </Td>
                    <Td>
                      <Text fontSize="sm" color="gray.600">{formatDate(invoice.issue_date)}</Text>
                    </Td>
                    <Td>
                      <Text fontSize="sm" color="gray.600">{formatDate(invoice.due_date)}</Text>
                    </Td>
                    <Td isNumeric>
                      <Text fontSize="sm" fontWeight="600" color="gray.800">
                        {formatCurrency(invoice.total, invoice.currency)}
                      </Text>
                    </Td>
                    <Td>
                      <Badge
                        colorScheme={statusColorScheme(invoice.status)}
                        borderRadius="full"
                        px={3}
                        py={1}
                        fontSize="xs"
                        textTransform="capitalize"
                      >
                        {invoice.status}
                      </Badge>
                    </Td>
                  </Tr>
                ))}
              </Tbody>
            </Table>
          </TableContainer>
        )}
      </GlassCard>

      {/* Delete confirm */}
      <AlertDialog isOpen={isOpen} leastDestructiveRef={cancelRef} onClose={onClose}>
        <AlertDialogOverlay>
          <AlertDialogContent borderRadius="xl">
            <AlertDialogHeader fontSize="lg" fontWeight="700" color="gray.800">
              Delete Client
            </AlertDialogHeader>
            <AlertDialogBody color="gray.600">
              Are you sure you want to delete{' '}
              <Text as="span" fontWeight="700" color="gray.800">{client.name}</Text>?
              This action cannot be undone. Clients with non-cancelled invoices cannot be deleted.
            </AlertDialogBody>
            <AlertDialogFooter gap={3}>
              <Button ref={cancelRef} onClick={onClose} variant="outline">
                Cancel
              </Button>
              <Button
                colorScheme="red"
                onClick={() => deleteMutation.mutate()}
                isLoading={deleteMutation.isPending}
                loadingText="Deleting..."
              >
                Delete
              </Button>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialogOverlay>
      </AlertDialog>
    </PageWrapper>
  );
}

export default function ClientDetailPage({ params }: { params: { id: string } }) {
  return (
    <ProtectedRoute>
      <AppShell>
        <ClientDetailContent id={Number(params.id)} />
      </AppShell>
    </ProtectedRoute>
  );
}
