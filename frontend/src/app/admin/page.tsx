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
  Stat,
  StatLabel,
  StatNumber,
  Input,
  InputGroup,
  InputLeftElement,
  Tooltip,
  IconButton,
} from '@chakra-ui/react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useEffect, useRef, useState } from 'react';
import { useRouter } from 'next/navigation';
import { ShieldCheck, Search, UserCheck, UserX, Users } from 'lucide-react';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { AppShell } from '@/components/layout/AppShell';
import { GlassCard } from '@/components/ui/GlassCard';
import { PageWrapper } from '@/components/layout/PageWrapper';
import { adminService } from '@/services/admin';
import type { AdminUser } from '@/services/admin';
import { useAuth } from '@/context/AuthContext';

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
}

function formatCurrency(amount: number): string {
  return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' }).format(amount);
}

function AdminContent() {
  const router = useRouter();
  const toast = useToast();
  const queryClient = useQueryClient();
  const { user } = useAuth();
  const [searchInput, setSearchInput] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');
  const searchTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const [targetUser, setTargetUser] = useState<AdminUser | null>(null);
  const { isOpen, onOpen, onClose } = useDisclosure();
  const cancelRef = useRef<HTMLButtonElement>(null);

  // Redirect if not admin
  useEffect(() => {
    if (user && !user.is_admin) {
      router.replace('/dashboard');
    }
  }, [user, router]);

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value;
    setSearchInput(val);
    if (searchTimerRef.current) clearTimeout(searchTimerRef.current);
    searchTimerRef.current = setTimeout(() => setDebouncedSearch(val), 300);
  };

  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['admin-stats'],
    queryFn: () => adminService.getStats(),
    enabled: !!user?.is_admin,
  });

  const { data: usersData, isLoading: usersLoading } = useQuery({
    queryKey: ['admin-users', debouncedSearch],
    queryFn: () => adminService.listUsers({ search: debouncedSearch || undefined, limit: 100 }),
    enabled: !!user?.is_admin,
  });

  const setStatusMutation = useMutation({
    mutationFn: ({ id, is_active }: { id: number; is_active: boolean }) =>
      adminService.setUserStatus(id, is_active),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-users'] });
      queryClient.invalidateQueries({ queryKey: ['admin-stats'] });
      toast({
        title: `User ${targetUser?.is_active ? 'deactivated' : 'activated'}`,
        status: 'success',
        duration: 3000,
        isClosable: true,
      });
      setTargetUser(null);
      onClose();
    },
    onError: () => {
      toast({ title: 'Failed to update user status', status: 'error', duration: 3000, isClosable: true });
    },
  });

  const handleToggleStatus = (u: AdminUser) => {
    setTargetUser(u);
    onOpen();
  };

  const handleConfirmToggle = () => {
    if (targetUser) {
      setStatusMutation.mutate({ id: targetUser.id, is_active: !targetUser.is_active });
    }
  };

  if (!user?.is_admin) {
    return (
      <Center py={20}>
        <Spinner size="xl" color="brand.500" />
      </Center>
    );
  }

  const users = usersData ?? [];

  return (
    <PageWrapper>
      {/* Header */}
      <HStack spacing={3} mb={8}>
        <ShieldCheck size={24} color="#4F46E5" />
        <Heading size="lg" color="gray.800">Admin Dashboard</Heading>
      </HStack>

      {/* Stats */}
      <SimpleGrid columns={{ base: 2, md: 4 }} spacing={4} mb={8}>
        {statsLoading ? (
          <Center py={8} gridColumn="1 / -1"><Spinner size="lg" color="brand.500" /></Center>
        ) : stats ? (
          <>
            <GlassCard>
              <Stat>
                <StatLabel color="gray.500" fontSize="xs" textTransform="uppercase" letterSpacing="wide">
                  Total Users
                </StatLabel>
                <StatNumber fontSize="2xl" color="gray.800">{stats.total_users}</StatNumber>
              </Stat>
            </GlassCard>
            <GlassCard>
              <Stat>
                <StatLabel color="gray.500" fontSize="xs" textTransform="uppercase" letterSpacing="wide">
                  Active Users
                </StatLabel>
                <StatNumber fontSize="2xl" color="green.500">{stats.active_users}</StatNumber>
              </Stat>
            </GlassCard>
            <GlassCard>
              <Stat>
                <StatLabel color="gray.500" fontSize="xs" textTransform="uppercase" letterSpacing="wide">
                  Total Invoices
                </StatLabel>
                <StatNumber fontSize="2xl" color="gray.800">{stats.total_invoices}</StatNumber>
              </Stat>
            </GlassCard>
            <GlassCard>
              <Stat>
                <StatLabel color="gray.500" fontSize="xs" textTransform="uppercase" letterSpacing="wide">
                  Total Revenue
                </StatLabel>
                <StatNumber fontSize="xl" color="brand.500">
                  {formatCurrency(stats.total_revenue)}
                </StatNumber>
              </Stat>
            </GlassCard>
          </>
        ) : null}
      </SimpleGrid>

      {/* Users table */}
      <GlassCard p={0} overflow="hidden">
        <Box p={4} borderBottom="1px solid" borderColor="gray.100">
          <HStack justify="space-between" flexWrap="wrap" gap={3}>
            <HStack spacing={2}>
              <Users size={18} color="#4F46E5" />
              <Heading size="sm" color="gray.700">Users</Heading>
              {!usersLoading && (
                <Badge colorScheme="purple" borderRadius="full" px={2} fontSize="xs">
                  {users.length}
                </Badge>
              )}
            </HStack>
            <InputGroup maxW="300px">
              <InputLeftElement pointerEvents="none">
                <Search size={14} color="#9CA3AF" />
              </InputLeftElement>
              <Input
                placeholder="Search users..."
                value={searchInput}
                onChange={handleSearchChange}
                focusBorderColor="brand.500"
                bg="gray.50"
                size="sm"
                border="1px solid"
                borderColor="gray.200"
              />
            </InputGroup>
          </HStack>
        </Box>

        {usersLoading ? (
          <Center py={12}><Spinner size="lg" color="brand.500" /></Center>
        ) : users.length === 0 ? (
          <Center py={12}>
            <VStack spacing={2}>
              <Users size={36} color="#CBD5E0" />
              <Text color="gray.400" fontSize="sm">No users found</Text>
            </VStack>
          </Center>
        ) : (
          <TableContainer>
            <Table variant="simple" size="sm">
              <Thead bg="gray.50">
                <Tr>
                  <Th fontSize="xs" textTransform="uppercase" color="gray.500">User</Th>
                  <Th fontSize="xs" textTransform="uppercase" color="gray.500">Email</Th>
                  <Th fontSize="xs" textTransform="uppercase" color="gray.500">Joined</Th>
                  <Th fontSize="xs" textTransform="uppercase" color="gray.500" isNumeric>Invoices</Th>
                  <Th fontSize="xs" textTransform="uppercase" color="gray.500">Roles</Th>
                  <Th fontSize="xs" textTransform="uppercase" color="gray.500">Status</Th>
                  <Th fontSize="xs" textTransform="uppercase" color="gray.500" isNumeric>Actions</Th>
                </Tr>
              </Thead>
              <Tbody>
                {users.map((u) => (
                  <Tr key={u.id} _hover={{ bg: 'gray.50' }}>
                    <Td>
                      <VStack align="flex-start" spacing={0}>
                        <Text fontSize="sm" fontWeight="600" color="gray.800">
                          {u.full_name ?? 'No name'}
                        </Text>
                        <Text fontSize="xs" color="gray.400">#{u.id}</Text>
                      </VStack>
                    </Td>
                    <Td>
                      <Text fontSize="sm" color="gray.600">{u.email}</Text>
                    </Td>
                    <Td>
                      <Text fontSize="sm" color="gray.600">{formatDate(u.created_at)}</Text>
                    </Td>
                    <Td isNumeric>
                      <Text fontSize="sm" color="gray.700">{u.invoice_count}</Text>
                    </Td>
                    <Td>
                      <HStack spacing={1}>
                        {u.is_admin && (
                          <Badge colorScheme="purple" borderRadius="full" px={2} fontSize="xs">
                            Admin
                          </Badge>
                        )}
                        {u.oauth_provider && (
                          <Badge colorScheme="blue" borderRadius="full" px={2} fontSize="xs">
                            {u.oauth_provider}
                          </Badge>
                        )}
                      </HStack>
                    </Td>
                    <Td>
                      <Badge
                        colorScheme={u.is_active ? 'green' : 'gray'}
                        borderRadius="full"
                        px={2}
                        fontSize="xs"
                      >
                        {u.is_active ? 'Active' : 'Inactive'}
                      </Badge>
                    </Td>
                    <Td isNumeric>
                      <Tooltip label={u.is_active ? 'Deactivate user' : 'Activate user'} hasArrow>
                        <IconButton
                          aria-label={u.is_active ? 'Deactivate' : 'Activate'}
                          icon={u.is_active ? <UserX size={15} /> : <UserCheck size={15} />}
                          size="sm"
                          variant="ghost"
                          colorScheme={u.is_active ? 'red' : 'green'}
                          onClick={() => handleToggleStatus(u)}
                          isDisabled={u.id === user?.id}
                        />
                      </Tooltip>
                    </Td>
                  </Tr>
                ))}
              </Tbody>
            </Table>
          </TableContainer>
        )}
      </GlassCard>

      {/* Confirm toggle */}
      <AlertDialog isOpen={isOpen} leastDestructiveRef={cancelRef} onClose={onClose}>
        <AlertDialogOverlay>
          <AlertDialogContent borderRadius="xl">
            <AlertDialogHeader fontSize="lg" fontWeight="700" color="gray.800">
              {targetUser?.is_active ? 'Deactivate User' : 'Activate User'}
            </AlertDialogHeader>
            <AlertDialogBody color="gray.600">
              Are you sure you want to {targetUser?.is_active ? 'deactivate' : 'activate'}{' '}
              <Text as="span" fontWeight="700" color="gray.800">
                {targetUser?.email}
              </Text>?
              {targetUser?.is_active && ' They will lose access to the platform.'}
            </AlertDialogBody>
            <AlertDialogFooter gap={3}>
              <Button ref={cancelRef} onClick={onClose} variant="outline">Cancel</Button>
              <Button
                colorScheme={targetUser?.is_active ? 'red' : 'green'}
                onClick={handleConfirmToggle}
                isLoading={setStatusMutation.isPending}
              >
                {targetUser?.is_active ? 'Deactivate' : 'Activate'}
              </Button>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialogOverlay>
      </AlertDialog>
    </PageWrapper>
  );
}

export default function AdminPage() {
  return (
    <ProtectedRoute>
      <AppShell>
        <AdminContent />
      </AppShell>
    </ProtectedRoute>
  );
}
