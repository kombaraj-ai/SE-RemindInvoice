'use client';
import {
  Heading,
  HStack,
  Badge,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  TableContainer,
  Tabs,
  TabList,
  Tab,
  TabPanels,
  TabPanel,
  Text,
  VStack,
  IconButton,
  Menu,
  MenuButton,
  MenuList,
  MenuItem,
  Spinner,
  Center,
  useToast,
  AlertDialog,
  AlertDialogBody,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogContent,
  AlertDialogOverlay,
  Button,
  useDisclosure,
  Tooltip,
} from '@chakra-ui/react';
import { FileText, MoreVertical, Plus, Send, CheckCircle, Copy, Eye } from 'lucide-react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useRouter } from 'next/navigation';
import { useRef, useState } from 'react';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { AppShell } from '@/components/layout/AppShell';
import { GlassCard } from '@/components/ui/GlassCard';
import { GradientButton } from '@/components/ui/GradientButton';
import { PageWrapper } from '@/components/layout/PageWrapper';
import { invoicesService } from '@/services/invoices';
import type { Invoice, InvoiceStatus } from '@/types/invoice';

const STATUS_TABS: Array<{ label: string; value: string | undefined }> = [
  { label: 'All', value: undefined },
  { label: 'Draft', value: 'draft' },
  { label: 'Sent', value: 'sent' },
  { label: 'Overdue', value: 'overdue' },
  { label: 'Paid', value: 'paid' },
];

function statusColorScheme(status: InvoiceStatus): string {
  switch (status) {
    case 'paid':
      return 'green';
    case 'overdue':
      return 'red';
    case 'sent':
      return 'blue';
    case 'viewed':
      return 'purple';
    case 'draft':
      return 'gray';
    case 'cancelled':
      return 'gray';
    default:
      return 'gray';
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

interface InvoiceTableProps {
  invoices: Invoice[];
  onSend: (id: number) => void;
  onMarkPaid: (id: number) => void;
  onDuplicate: (id: number) => void;
  isMutating: boolean;
}

function InvoiceTable({ invoices, onSend, onMarkPaid, onDuplicate, isMutating }: InvoiceTableProps) {
  const router = useRouter();

  if (invoices.length === 0) {
    return (
      <Center py={16}>
        <VStack spacing={4}>
          <FileText size={48} color="#CBD5E0" />
          <Text color="gray.400" fontSize="sm" fontWeight="500">
            No invoices found
          </Text>
          <Text color="gray.400" fontSize="xs">
            Create your first invoice to get started
          </Text>
        </VStack>
      </Center>
    );
  }

  return (
    <TableContainer>
      <Table variant="simple">
        <Thead bg="gray.50">
          <Tr>
            <Th fontSize="xs" textTransform="uppercase" letterSpacing="wider" color="gray.500">
              Invoice #
            </Th>
            <Th fontSize="xs" textTransform="uppercase" letterSpacing="wider" color="gray.500">
              Client
            </Th>
            <Th fontSize="xs" textTransform="uppercase" letterSpacing="wider" color="gray.500">
              Issue Date
            </Th>
            <Th fontSize="xs" textTransform="uppercase" letterSpacing="wider" color="gray.500">
              Due Date
            </Th>
            <Th fontSize="xs" textTransform="uppercase" letterSpacing="wider" color="gray.500" isNumeric>
              Amount
            </Th>
            <Th fontSize="xs" textTransform="uppercase" letterSpacing="wider" color="gray.500">
              Status
            </Th>
            <Th />
          </Tr>
        </Thead>
        <Tbody>
          {invoices.map((invoice) => (
            <Tr
              key={invoice.id}
              _hover={{ bg: 'gray.50', cursor: 'pointer' }}
              onClick={() => router.push(`/invoices/${invoice.id}`)}
            >
              <Td>
                <Text fontSize="sm" fontWeight="600" color="brand.500">
                  {invoice.invoice_number}
                </Text>
              </Td>
              <Td>
                <Text fontSize="sm" color="gray.700">
                  {invoice.client?.name ?? `Client #${invoice.client_id}`}
                </Text>
                {invoice.client?.company_name && (
                  <Text fontSize="xs" color="gray.400">
                    {invoice.client.company_name}
                  </Text>
                )}
              </Td>
              <Td>
                <Text fontSize="sm" color="gray.600">
                  {formatDate(invoice.issue_date)}
                </Text>
              </Td>
              <Td>
                <Text fontSize="sm" color="gray.600">
                  {formatDate(invoice.due_date)}
                </Text>
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
              <Td onClick={(e) => e.stopPropagation()}>
                <HStack spacing={1}>
                  <Tooltip label="View">
                    <IconButton
                      aria-label="View invoice"
                      icon={<Eye size={14} />}
                      size="xs"
                      variant="ghost"
                      colorScheme="gray"
                      onClick={() => router.push(`/invoices/${invoice.id}`)}
                    />
                  </Tooltip>
                  <Menu>
                    <MenuButton
                      as={IconButton}
                      aria-label="More actions"
                      icon={<MoreVertical size={14} />}
                      size="xs"
                      variant="ghost"
                      colorScheme="gray"
                      isDisabled={isMutating}
                    />
                    <MenuList fontSize="sm" shadow="lg" border="1px solid" borderColor="gray.100">
                      {(invoice.status === 'draft' || invoice.status === 'sent') && (
                        <MenuItem
                          icon={<Send size={14} />}
                          onClick={() => onSend(invoice.id)}
                          color="blue.600"
                        >
                          Send Invoice
                        </MenuItem>
                      )}
                      {(invoice.status === 'sent' || invoice.status === 'overdue') && (
                        <MenuItem
                          icon={<CheckCircle size={14} />}
                          onClick={() => onMarkPaid(invoice.id)}
                          color="green.600"
                        >
                          Mark as Paid
                        </MenuItem>
                      )}
                      <MenuItem
                        icon={<Copy size={14} />}
                        onClick={() => onDuplicate(invoice.id)}
                      >
                        Duplicate
                      </MenuItem>
                    </MenuList>
                  </Menu>
                </HStack>
              </Td>
            </Tr>
          ))}
        </Tbody>
      </Table>
    </TableContainer>
  );
}

export default function InvoicesPage() {
  const router = useRouter();
  const toast = useToast();
  const queryClient = useQueryClient();
  const [activeTabIndex, setActiveTabIndex] = useState(0);
  const [confirmAction, setConfirmAction] = useState<{
    type: 'send' | 'markPaid';
    invoiceId: number;
  } | null>(null);
  const { isOpen, onOpen, onClose } = useDisclosure();
  const cancelRef = useRef<HTMLButtonElement>(null);

  const activeStatus = STATUS_TABS[activeTabIndex]?.value;

  const { data, isLoading } = useQuery({
    queryKey: ['invoices', activeStatus],
    queryFn: () => invoicesService.list({ status: activeStatus }),
  });

  const sendMutation = useMutation({
    mutationFn: (id: number) => invoicesService.send(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['invoices'] });
      toast({ title: 'Invoice sent successfully', status: 'success', duration: 3000, isClosable: true });
      onClose();
    },
    onError: () => {
      toast({ title: 'Failed to send invoice', status: 'error', duration: 3000, isClosable: true });
    },
  });

  const markPaidMutation = useMutation({
    mutationFn: (id: number) => invoicesService.markPaid(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['invoices'] });
      toast({ title: 'Invoice marked as paid', status: 'success', duration: 3000, isClosable: true });
      onClose();
    },
    onError: () => {
      toast({ title: 'Failed to mark invoice as paid', status: 'error', duration: 3000, isClosable: true });
    },
  });

  const duplicateMutation = useMutation({
    mutationFn: (id: number) => invoicesService.duplicate(id),
    onSuccess: (duplicated) => {
      queryClient.invalidateQueries({ queryKey: ['invoices'] });
      toast({ title: 'Invoice duplicated', status: 'success', duration: 3000, isClosable: true });
      router.push(`/invoices/${duplicated.id}/edit`);
    },
    onError: () => {
      toast({ title: 'Failed to duplicate invoice', status: 'error', duration: 3000, isClosable: true });
    },
  });

  const handleSend = (id: number) => {
    setConfirmAction({ type: 'send', invoiceId: id });
    onOpen();
  };

  const handleMarkPaid = (id: number) => {
    setConfirmAction({ type: 'markPaid', invoiceId: id });
    onOpen();
  };

  const handleConfirm = () => {
    if (!confirmAction) return;
    if (confirmAction.type === 'send') {
      sendMutation.mutate(confirmAction.invoiceId);
    } else {
      markPaidMutation.mutate(confirmAction.invoiceId);
    }
  };

  const isMutating =
    sendMutation.isPending || markPaidMutation.isPending || duplicateMutation.isPending;

  const invoices = data?.items ?? [];

  return (
    <ProtectedRoute>
      <AppShell>
        <PageWrapper>
          <HStack justify="space-between" mb={8}>
            <HStack spacing={3}>
              <FileText size={24} color="#4F46E5" />
              <Heading size="lg" color="gray.800">
                Invoices
              </Heading>
              {data && (
                <Badge colorScheme="brand" borderRadius="full" px={2} fontSize="xs">
                  {data.total}
                </Badge>
              )}
            </HStack>
            <GradientButton
              leftIcon={<Plus size={16} />}
              onClick={() => router.push('/invoices/new')}
            >
              New Invoice
            </GradientButton>
          </HStack>

          <GlassCard p={0} overflow="hidden">
            <Tabs
              index={activeTabIndex}
              onChange={setActiveTabIndex}
              colorScheme="brand"
              variant="enclosed-colored"
            >
              <TabList bg="gray.50" borderBottom="1px solid" borderColor="gray.200" px={4} pt={2}>
                {STATUS_TABS.map((tab) => (
                  <Tab
                    key={tab.label}
                    fontSize="sm"
                    fontWeight="500"
                    color="gray.600"
                    _selected={{ color: 'brand.500', bg: 'white', borderColor: 'gray.200' }}
                  >
                    {tab.label}
                  </Tab>
                ))}
              </TabList>

              <TabPanels>
                {STATUS_TABS.map((tab) => (
                  <TabPanel key={tab.label} p={0}>
                    {isLoading ? (
                      <Center py={16}>
                        <Spinner size="lg" color="brand.500" />
                      </Center>
                    ) : (
                      <InvoiceTable
                        invoices={invoices}
                        onSend={handleSend}
                        onMarkPaid={handleMarkPaid}
                        onDuplicate={(id) => duplicateMutation.mutate(id)}
                        isMutating={isMutating}
                      />
                    )}
                  </TabPanel>
                ))}
              </TabPanels>
            </Tabs>
          </GlassCard>

          <AlertDialog isOpen={isOpen} leastDestructiveRef={cancelRef} onClose={onClose}>
            <AlertDialogOverlay>
              <AlertDialogContent borderRadius="xl">
                <AlertDialogHeader fontSize="lg" fontWeight="bold">
                  {confirmAction?.type === 'send' ? 'Send Invoice' : 'Mark as Paid'}
                </AlertDialogHeader>
                <AlertDialogBody>
                  {confirmAction?.type === 'send'
                    ? 'This will send the invoice to the client via email. Are you sure?'
                    : 'This will mark the invoice as paid. This action cannot be undone easily.'}
                </AlertDialogBody>
                <AlertDialogFooter gap={3}>
                  <Button ref={cancelRef} onClick={onClose} variant="ghost">
                    Cancel
                  </Button>
                  <Button
                    colorScheme={confirmAction?.type === 'send' ? 'blue' : 'green'}
                    onClick={handleConfirm}
                    isLoading={sendMutation.isPending || markPaidMutation.isPending}
                  >
                    {confirmAction?.type === 'send' ? 'Send' : 'Mark Paid'}
                  </Button>
                </AlertDialogFooter>
              </AlertDialogContent>
            </AlertDialogOverlay>
          </AlertDialog>
        </PageWrapper>
      </AppShell>
    </ProtectedRoute>
  );
}
