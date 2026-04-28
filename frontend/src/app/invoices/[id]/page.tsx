'use client';
import {
  Box,
  Button,
  HStack,
  Heading,
  Text,
  Badge,
  VStack,
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
  useToast,
  useDisclosure,
  AlertDialog,
  AlertDialogBody,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogContent,
  AlertDialogOverlay,
  SimpleGrid,
} from '@chakra-ui/react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useRouter } from 'next/navigation';
import { useRef, useState } from 'react';
import {
  ArrowLeft,
  FileText,
  Send,
  CheckCircle,
  Copy,
  Trash2,
  Edit,
  ExternalLink,
  Download,
} from 'lucide-react';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { AppShell } from '@/components/layout/AppShell';
import { GlassCard } from '@/components/ui/GlassCard';
import { GradientButton } from '@/components/ui/GradientButton';
import { PageWrapper } from '@/components/layout/PageWrapper';
import { invoicesService } from '@/services/invoices';
import { remindersService } from '@/services/reminders';
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

type ActionType = 'send' | 'markPaid' | 'delete';

function InvoiceDetailContent({ id }: { id: number }) {
  const router = useRouter();
  const toast = useToast();
  const queryClient = useQueryClient();
  const { isOpen, onOpen, onClose } = useDisclosure();
  const cancelRef = useRef<HTMLButtonElement>(null);
  const actionRef = useRef<ActionType | null>(null);
  const [isDownloading, setIsDownloading] = useState(false);

  const handleDownloadPdf = async () => {
    if (!invoice) return;
    setIsDownloading(true);
    try {
      const apiBase = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000/api/v1';
      const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
      const res = await fetch(`${apiBase}/invoices/${id}/pdf`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (!res.ok) throw new Error('Failed to download PDF');
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${invoice.invoice_number}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      toast({ title: 'PDF download failed', status: 'error', duration: 3000, isClosable: true });
    } finally {
      setIsDownloading(false);
    }
  };

  const { data: invoice, isLoading, isError } = useQuery({
    queryKey: ['invoice', id],
    queryFn: () => invoicesService.get(id),
  });

  const { data: reminderLogs } = useQuery({
    queryKey: ['reminder-logs', id],
    queryFn: () => remindersService.getLogs(id),
    enabled: !!id,
  });

  const sendMutation = useMutation({
    mutationFn: () => invoicesService.send(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['invoice', id] });
      queryClient.invalidateQueries({ queryKey: ['invoices'] });
      toast({ title: 'Invoice sent successfully', status: 'success', duration: 3000, isClosable: true });
      onClose();
    },
    onError: () => {
      toast({ title: 'Failed to send invoice', status: 'error', duration: 3000, isClosable: true });
    },
  });

  const markPaidMutation = useMutation({
    mutationFn: () => invoicesService.markPaid(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['invoice', id] });
      queryClient.invalidateQueries({ queryKey: ['invoices'] });
      toast({ title: 'Invoice marked as paid', status: 'success', duration: 3000, isClosable: true });
      onClose();
    },
    onError: () => {
      toast({ title: 'Failed to mark as paid', status: 'error', duration: 3000, isClosable: true });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: () => invoicesService.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['invoices'] });
      toast({ title: 'Invoice deleted', status: 'success', duration: 3000, isClosable: true });
      router.push('/invoices');
    },
    onError: () => {
      toast({ title: 'Failed to delete invoice', status: 'error', duration: 3000, isClosable: true });
    },
  });

  const duplicateMutation = useMutation({
    mutationFn: () => invoicesService.duplicate(id),
    onSuccess: (dup) => {
      queryClient.invalidateQueries({ queryKey: ['invoices'] });
      toast({ title: 'Invoice duplicated', status: 'success', duration: 3000, isClosable: true });
      router.push(`/invoices/${dup.id}/edit`);
    },
    onError: () => {
      toast({ title: 'Failed to duplicate invoice', status: 'error', duration: 3000, isClosable: true });
    },
  });

  const openConfirm = (action: ActionType) => {
    actionRef.current = action;
    onOpen();
  };

  const handleConfirm = () => {
    const action = actionRef.current;
    if (action === 'send') sendMutation.mutate();
    else if (action === 'markPaid') markPaidMutation.mutate();
    else if (action === 'delete') deleteMutation.mutate();
  };

  const isAnyMutating =
    sendMutation.isPending ||
    markPaidMutation.isPending ||
    deleteMutation.isPending ||
    duplicateMutation.isPending;

  if (isLoading) {
    return (
      <Center py={20}>
        <Spinner size="xl" color="brand.500" />
      </Center>
    );
  }

  if (isError || !invoice) {
    return (
      <Center py={20}>
        <VStack spacing={3}>
          <Text color="red.500" fontWeight="600">Invoice not found</Text>
          <Button variant="ghost" onClick={() => router.push('/invoices')}>
            Back to Invoices
          </Button>
        </VStack>
      </Center>
    );
  }

  const status = invoice.status;
  const isDraft = status === 'draft';
  const isSentOrViewed = status === 'sent' || status === 'viewed' || status === 'overdue';
  const publicUrl = `/invoices/public/${invoice.public_token}`;

  const confirmTitle =
    actionRef.current === 'send'
      ? 'Send Invoice'
      : actionRef.current === 'markPaid'
      ? 'Mark as Paid'
      : 'Delete Invoice';

  const confirmBody =
    actionRef.current === 'send'
      ? 'This will email the invoice to the client and mark it as sent.'
      : actionRef.current === 'markPaid'
      ? 'This will mark the invoice as paid. This cannot be easily undone.'
      : 'This will permanently delete the draft invoice. This cannot be undone.';

  return (
    <PageWrapper>
      {/* Header */}
      <HStack justify="space-between" mb={8} flexWrap="wrap" gap={3}>
        <HStack spacing={3}>
          <Button
            leftIcon={<ArrowLeft size={16} />}
            variant="ghost"
            size="sm"
            onClick={() => router.push('/invoices')}
            color="gray.600"
          >
            Invoices
          </Button>
          <FileText size={24} color="#4F46E5" />
          <Heading size="lg" color="gray.800">
            {invoice.invoice_number}
          </Heading>
          <Badge
            colorScheme={statusColorScheme(status)}
            borderRadius="full"
            px={3}
            py={1}
            fontSize="sm"
            textTransform="capitalize"
          >
            {status}
          </Badge>
        </HStack>

        <HStack spacing={2} flexWrap="wrap">
          <Button
            leftIcon={<ExternalLink size={14} />}
            variant="ghost"
            size="sm"
            color="gray.600"
            onClick={() => window.open(publicUrl, '_blank')}
          >
            Public View
          </Button>
          <Button
            leftIcon={<Download size={14} />}
            variant="ghost"
            size="sm"
            color="gray.600"
            onClick={handleDownloadPdf}
            isLoading={isDownloading}
            loadingText="Generating..."
          >
            Download PDF
          </Button>

          {isDraft && (
            <>
              <Button
                leftIcon={<Edit size={16} />}
                variant="outline"
                colorScheme="brand"
                onClick={() => router.push(`/invoices/${id}/edit`)}
                isDisabled={isAnyMutating}
              >
                Edit
              </Button>
              <GradientButton
                leftIcon={<Send size={16} />}
                onClick={() => openConfirm('send')}
                isDisabled={isAnyMutating}
              >
                Send Invoice
              </GradientButton>
              <Button
                leftIcon={<Trash2 size={16} />}
                colorScheme="red"
                variant="outline"
                onClick={() => openConfirm('delete')}
                isDisabled={isAnyMutating}
              >
                Delete
              </Button>
            </>
          )}

          {isSentOrViewed && (
            <>
              <Button
                leftIcon={<CheckCircle size={16} />}
                colorScheme="green"
                variant="outline"
                onClick={() => openConfirm('markPaid')}
                isDisabled={isAnyMutating}
              >
                Mark Paid
              </Button>
              <Button
                leftIcon={<Copy size={16} />}
                variant="outline"
                onClick={() => duplicateMutation.mutate()}
                isLoading={duplicateMutation.isPending}
              >
                Duplicate
              </Button>
            </>
          )}

          {(status === 'paid' || status === 'cancelled') && (
            <Button
              leftIcon={<Copy size={16} />}
              variant="outline"
              onClick={() => duplicateMutation.mutate()}
              isLoading={duplicateMutation.isPending}
            >
              Duplicate
            </Button>
          )}
        </HStack>
      </HStack>

      {/* Info row */}
      <SimpleGrid columns={{ base: 1, md: 2 }} spacing={6} mb={6}>
        <GlassCard>
          <Heading size="sm" color="gray.700" mb={4}>Invoice Details</Heading>
          <VStack align="stretch" spacing={2}>
            <HStack justify="space-between">
              <Text fontSize="sm" color="gray.500">Invoice Number</Text>
              <Text fontSize="sm" fontWeight="600" color="brand.500">{invoice.invoice_number}</Text>
            </HStack>
            <Divider />
            <HStack justify="space-between">
              <Text fontSize="sm" color="gray.500">Issue Date</Text>
              <Text fontSize="sm" color="gray.700">{formatDate(invoice.issue_date)}</Text>
            </HStack>
            <Divider />
            <HStack justify="space-between">
              <Text fontSize="sm" color="gray.500">Due Date</Text>
              <Text fontSize="sm" color="gray.700">{formatDate(invoice.due_date)}</Text>
            </HStack>
            <Divider />
            <HStack justify="space-between">
              <Text fontSize="sm" color="gray.500">Currency</Text>
              <Text fontSize="sm" color="gray.700">{invoice.currency}</Text>
            </HStack>
            {invoice.sent_at && (
              <>
                <Divider />
                <HStack justify="space-between">
                  <Text fontSize="sm" color="gray.500">Sent At</Text>
                  <Text fontSize="sm" color="gray.700">{formatDate(invoice.sent_at)}</Text>
                </HStack>
              </>
            )}
            {invoice.paid_at && (
              <>
                <Divider />
                <HStack justify="space-between">
                  <Text fontSize="sm" color="gray.500">Paid At</Text>
                  <Text fontSize="sm" color="green.600">{formatDate(invoice.paid_at)}</Text>
                </HStack>
              </>
            )}
          </VStack>
        </GlassCard>

        <GlassCard>
          <Heading size="sm" color="gray.700" mb={4}>Client</Heading>
          {invoice.client ? (
            <VStack align="stretch" spacing={2}>
              <Text fontSize="sm" fontWeight="600" color="gray.800">{invoice.client.name}</Text>
              {invoice.client.company_name && (
                <Text fontSize="sm" color="gray.500">{invoice.client.company_name}</Text>
              )}
              <Text fontSize="sm" color="gray.600">{invoice.client.email}</Text>
              {invoice.client.phone && (
                <Text fontSize="sm" color="gray.600">{invoice.client.phone}</Text>
              )}
              <Box mt={2}>
                <Button
                  size="xs"
                  variant="ghost"
                  colorScheme="brand"
                  onClick={() => router.push(`/clients/${invoice.client_id}`)}
                >
                  View Client Profile
                </Button>
              </Box>
            </VStack>
          ) : (
            <Text fontSize="sm" color="gray.400">Client #{invoice.client_id}</Text>
          )}
        </GlassCard>
      </SimpleGrid>

      {/* Line items */}
      <GlassCard p={0} overflow="hidden" mb={6}>
        <Box px={6} py={4} borderBottom="1px solid" borderColor="gray.100">
          <Heading size="sm" color="gray.700">Line Items</Heading>
        </Box>
        <TableContainer>
          <Table variant="simple" size="sm">
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
        <Box px={6} py={4} borderTop="1px solid" borderColor="gray.100" bg="gray.50">
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
                <Text fontSize="sm" color="red.500">
                  -{formatCurrency(invoice.discount_amount, invoice.currency)}
                </Text>
              </HStack>
            )}
            <Divider w="280px" />
            <HStack justify="space-between" w="280px">
              <Text fontSize="md" fontWeight="700" color="gray.800">Total</Text>
              <Text fontSize="md" fontWeight="700" color="brand.500">
                {formatCurrency(invoice.total, invoice.currency)}
              </Text>
            </HStack>
          </VStack>
        </Box>
      </GlassCard>

      {/* Notes */}
      {invoice.notes && (
        <GlassCard mb={6}>
          <Heading size="sm" color="gray.700" mb={3}>Notes</Heading>
          <Text fontSize="sm" color="gray.600" whiteSpace="pre-wrap">{invoice.notes}</Text>
        </GlassCard>
      )}

      {/* Reminder Logs */}
      {reminderLogs && reminderLogs.length > 0 && (
        <GlassCard p={0} overflow="hidden">
          <Box px={6} py={4} borderBottom="1px solid" borderColor="gray.100">
            <Heading size="sm" color="gray.700">Reminder History</Heading>
          </Box>
          <TableContainer>
            <Table variant="simple" size="sm">
              <Thead bg="gray.50">
                <Tr>
                  <Th fontSize="xs" textTransform="uppercase" color="gray.500">Sent At</Th>
                  <Th fontSize="xs" textTransform="uppercase" color="gray.500">Email To</Th>
                  <Th fontSize="xs" textTransform="uppercase" color="gray.500">Subject</Th>
                  <Th fontSize="xs" textTransform="uppercase" color="gray.500">Status</Th>
                </Tr>
              </Thead>
              <Tbody>
                {reminderLogs.map((log) => (
                  <Tr key={log.id}>
                    <Td><Text fontSize="sm" color="gray.600">{formatDate(log.sent_at)}</Text></Td>
                    <Td><Text fontSize="sm" color="gray.600">{log.email_to}</Text></Td>
                    <Td><Text fontSize="sm" color="gray.600">{log.subject}</Text></Td>
                    <Td>
                      <Badge
                        colorScheme={log.status === 'sent' ? 'green' : 'red'}
                        borderRadius="full"
                        px={2}
                        fontSize="xs"
                        textTransform="capitalize"
                      >
                        {log.status}
                      </Badge>
                    </Td>
                  </Tr>
                ))}
              </Tbody>
            </Table>
          </TableContainer>
        </GlassCard>
      )}

      {/* Confirm dialog */}
      <AlertDialog isOpen={isOpen} leastDestructiveRef={cancelRef} onClose={onClose}>
        <AlertDialogOverlay>
          <AlertDialogContent borderRadius="xl">
            <AlertDialogHeader fontSize="lg" fontWeight="700" color="gray.800">
              {confirmTitle}
            </AlertDialogHeader>
            <AlertDialogBody color="gray.600">{confirmBody}</AlertDialogBody>
            <AlertDialogFooter gap={3}>
              <Button ref={cancelRef} onClick={onClose} variant="outline">
                Cancel
              </Button>
              <Button
                colorScheme={
                  actionRef.current === 'delete'
                    ? 'red'
                    : actionRef.current === 'markPaid'
                    ? 'green'
                    : 'blue'
                }
                onClick={handleConfirm}
                isLoading={sendMutation.isPending || markPaidMutation.isPending || deleteMutation.isPending}
              >
                {actionRef.current === 'delete'
                  ? 'Delete'
                  : actionRef.current === 'markPaid'
                  ? 'Mark Paid'
                  : 'Send'}
              </Button>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialogOverlay>
      </AlertDialog>
    </PageWrapper>
  );
}

export default function InvoiceDetailPage({ params }: { params: { id: string } }) {
  return (
    <ProtectedRoute>
      <AppShell>
        <InvoiceDetailContent id={Number(params.id)} />
      </AppShell>
    </ProtectedRoute>
  );
}
