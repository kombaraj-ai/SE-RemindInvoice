'use client';
import {
  Box,
  Button,
  HStack,
  Heading,
  Input,
  InputGroup,
  InputLeftElement,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Text,
  Badge,
  IconButton,
  Tooltip,
  useToast,
  useDisclosure,
  AlertDialog,
  AlertDialogBody,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogContent,
  AlertDialogOverlay,
  Spinner,
  Center,
  VStack,
  TableContainer,
} from '@chakra-ui/react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useRouter } from 'next/navigation';
import { useRef, useState, useCallback } from 'react';
import { Users, Search, Plus, Trash2, Eye } from 'lucide-react';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { AppShell } from '@/components/layout/AppShell';
import { GlassCard } from '@/components/ui/GlassCard';
import { GradientButton } from '@/components/ui/GradientButton';
import { PageWrapper } from '@/components/layout/PageWrapper';
import { clientsService } from '@/services/clients';
import type { Client } from '@/types/client';

function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const debounced = useCallback(
    (val: T) => {
      if (timerRef.current) clearTimeout(timerRef.current);
      timerRef.current = setTimeout(() => setDebouncedValue(val), delay);
    },
    [delay]
  );

  return debouncedValue;
}

function ClientsContent() {
  const router = useRouter();
  const toast = useToast();
  const queryClient = useQueryClient();
  const { isOpen, onOpen, onClose } = useDisclosure();
  const cancelRef = useRef<HTMLButtonElement>(null);

  const [searchInput, setSearchInput] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');
  const searchTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const [clientToDelete, setClientToDelete] = useState<Client | null>(null);

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value;
    setSearchInput(val);
    if (searchTimerRef.current) clearTimeout(searchTimerRef.current);
    searchTimerRef.current = setTimeout(() => setDebouncedSearch(val), 300);
  };

  const { data, isLoading, isError } = useQuery({
    queryKey: ['clients', debouncedSearch],
    queryFn: () => clientsService.list({ search: debouncedSearch || undefined }),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => clientsService.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['clients'] });
      toast({
        title: 'Client deleted',
        description: `${clientToDelete?.name} has been deleted.`,
        status: 'success',
        duration: 3000,
        isClosable: true,
      });
      setClientToDelete(null);
      onClose();
    },
    onError: () => {
      toast({
        title: 'Delete failed',
        description: 'Could not delete the client. Please try again.',
        status: 'error',
        duration: 3000,
        isClosable: true,
      });
    },
  });

  const handleDeleteClick = (client: Client, e: React.MouseEvent) => {
    e.stopPropagation();
    setClientToDelete(client);
    onOpen();
  };

  const handleConfirmDelete = () => {
    if (clientToDelete) {
      deleteMutation.mutate(clientToDelete.id);
    }
  };

  const formatCurrency = (amount: number, currency: string) => {
    return new Intl.NumberFormat('en-IN', { style: 'currency', currency }).format(amount);
  };

  const clients = data?.items ?? [];
  const total = data?.total ?? 0;

  return (
    <PageWrapper>
      <HStack justify="space-between" mb={8}>
        <HStack spacing={3}>
          <Users size={24} color="#4F46E5" />
          <Heading size="lg" color="gray.800">
            Clients
          </Heading>
          {!isLoading && (
            <Badge colorScheme="purple" borderRadius="full" px={3} fontSize="sm">
              {total}
            </Badge>
          )}
        </HStack>
        <GradientButton
          leftIcon={<Plus size={16} />}
          onClick={() => router.push('/clients/new')}
        >
          New Client
        </GradientButton>
      </HStack>

      <GlassCard p={0} overflow="hidden">
        {/* Search bar */}
        <Box p={4} borderBottom="1px solid" borderColor="gray.100">
          <InputGroup maxW="360px">
            <InputLeftElement pointerEvents="none">
              <Search size={16} color="#9CA3AF" />
            </InputLeftElement>
            <Input
              placeholder="Search clients..."
              value={searchInput}
              onChange={handleSearchChange}
              focusBorderColor="brand.500"
              bg="gray.50"
              border="1px solid"
              borderColor="gray.200"
              _hover={{ borderColor: 'gray.300' }}
            />
          </InputGroup>
        </Box>

        {/* Table */}
        {isLoading ? (
          <Center py={16}>
            <Spinner size="xl" color="brand.500" />
          </Center>
        ) : isError ? (
          <Center py={16}>
            <VStack spacing={3}>
              <Text color="red.500" fontWeight="600">
                Failed to load clients
              </Text>
              <Text color="gray.500" fontSize="sm">
                Please refresh the page to try again.
              </Text>
            </VStack>
          </Center>
        ) : clients.length === 0 ? (
          <Center py={16}>
            <VStack spacing={3}>
              <Users size={40} color="#CBD5E0" />
              <Text color="gray.500" fontWeight="600">
                {debouncedSearch ? 'No clients match your search' : 'No clients yet'}
              </Text>
              <Text color="gray.400" fontSize="sm">
                {debouncedSearch
                  ? 'Try a different search term.'
                  : 'Add your first client to get started.'}
              </Text>
              {!debouncedSearch && (
                <GradientButton size="sm" onClick={() => router.push('/clients/new')}>
                  Add Client
                </GradientButton>
              )}
            </VStack>
          </Center>
        ) : (
          <TableContainer>
            <Table variant="simple">
              <Thead bg="gray.50">
                <Tr>
                  <Th color="gray.500" fontSize="xs" fontWeight="600" textTransform="uppercase">
                    Name
                  </Th>
                  <Th color="gray.500" fontSize="xs" fontWeight="600" textTransform="uppercase">
                    Company
                  </Th>
                  <Th color="gray.500" fontSize="xs" fontWeight="600" textTransform="uppercase">
                    Email
                  </Th>
                  <Th color="gray.500" fontSize="xs" fontWeight="600" textTransform="uppercase">
                    Currency
                  </Th>
                  <Th color="gray.500" fontSize="xs" fontWeight="600" textTransform="uppercase">
                    Status
                  </Th>
                  <Th color="gray.500" fontSize="xs" fontWeight="600" textTransform="uppercase" isNumeric>
                    Actions
                  </Th>
                </Tr>
              </Thead>
              <Tbody>
                {clients.map((client) => (
                  <Tr
                    key={client.id}
                    cursor="pointer"
                    _hover={{ bg: 'brand.50' }}
                    transition="background 0.15s"
                    onClick={() => router.push(`/clients/${client.id}`)}
                  >
                    <Td>
                      <Text fontWeight="600" color="gray.800" fontSize="sm">
                        {client.name}
                      </Text>
                    </Td>
                    <Td>
                      <Text color="gray.600" fontSize="sm">
                        {client.company_name ?? '—'}
                      </Text>
                    </Td>
                    <Td>
                      <Text color="gray.600" fontSize="sm">
                        {client.email}
                      </Text>
                    </Td>
                    <Td>
                      <Text color="gray.600" fontSize="sm">
                        {client.currency}
                      </Text>
                    </Td>
                    <Td>
                      <Badge
                        colorScheme={client.is_active ? 'green' : 'gray'}
                        borderRadius="full"
                        px={2}
                        fontSize="xs"
                      >
                        {client.is_active ? 'Active' : 'Inactive'}
                      </Badge>
                    </Td>
                    <Td isNumeric>
                      <HStack spacing={1} justify="flex-end">
                        <Tooltip label="View details" hasArrow>
                          <IconButton
                            aria-label="View client"
                            icon={<Eye size={15} />}
                            size="sm"
                            variant="ghost"
                            colorScheme="brand"
                            onClick={(e) => {
                              e.stopPropagation();
                              router.push(`/clients/${client.id}`);
                            }}
                          />
                        </Tooltip>
                        <Tooltip label="Delete client" hasArrow>
                          <IconButton
                            aria-label="Delete client"
                            icon={<Trash2 size={15} />}
                            size="sm"
                            variant="ghost"
                            colorScheme="red"
                            onClick={(e) => handleDeleteClick(client, e)}
                          />
                        </Tooltip>
                      </HStack>
                    </Td>
                  </Tr>
                ))}
              </Tbody>
            </Table>
          </TableContainer>
        )}
      </GlassCard>

      {/* Delete confirmation dialog */}
      <AlertDialog isOpen={isOpen} leastDestructiveRef={cancelRef} onClose={onClose}>
        <AlertDialogOverlay>
          <AlertDialogContent borderRadius="xl">
            <AlertDialogHeader fontSize="lg" fontWeight="700" color="gray.800">
              Delete Client
            </AlertDialogHeader>
            <AlertDialogBody color="gray.600">
              Are you sure you want to delete{' '}
              <Text as="span" fontWeight="700" color="gray.800">
                {clientToDelete?.name}
              </Text>
              ? This action cannot be undone and will remove all associated data.
            </AlertDialogBody>
            <AlertDialogFooter gap={3}>
              <Button ref={cancelRef} onClick={onClose} variant="outline">
                Cancel
              </Button>
              <Button
                colorScheme="red"
                onClick={handleConfirmDelete}
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

export default function ClientsPage() {
  return (
    <ProtectedRoute>
      <AppShell>
        <ClientsContent />
      </AppShell>
    </ProtectedRoute>
  );
}
