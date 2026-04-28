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
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalFooter,
  ModalCloseButton,
  FormControl,
  FormLabel,
  FormErrorMessage,
  Input,
  Select,
  Switch,
  IconButton,
  Tooltip,
  Divider,
} from '@chakra-ui/react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useRef, useState } from 'react';
import { Bell, Plus, Trash2 } from 'lucide-react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { AppShell } from '@/components/layout/AppShell';
import { GlassCard } from '@/components/ui/GlassCard';
import { GradientButton } from '@/components/ui/GradientButton';
import { PageWrapper } from '@/components/layout/PageWrapper';
import { remindersService } from '@/services/reminders';
import type { ReminderRule, TriggerType } from '@/types/reminder';

const ruleSchema = z.object({
  name: z.string().min(1, 'Name is required'),
  trigger_type: z.enum(['before_due', 'on_due', 'after_due'] as const),
  days_offset: z.number({ invalid_type_error: 'Must be a number' }).int().min(0, 'Must be >= 0'),
});

type RuleFormValues = z.infer<typeof ruleSchema>;

const TRIGGER_LABELS: Record<TriggerType, string> = {
  before_due: 'Before Due Date',
  on_due: 'On Due Date',
  after_due: 'After Due Date',
};

function triggerColorScheme(type: TriggerType): string {
  switch (type) {
    case 'before_due': return 'blue';
    case 'on_due': return 'orange';
    case 'after_due': return 'red';
  }
}

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

function RemindersContent() {
  const toast = useToast();
  const queryClient = useQueryClient();
  const [ruleToDelete, setRuleToDelete] = useState<ReminderRule | null>(null);
  const cancelRef = useRef<HTMLButtonElement>(null);
  const {
    isOpen: isDeleteOpen,
    onOpen: onDeleteOpen,
    onClose: onDeleteClose,
  } = useDisclosure();
  const {
    isOpen: isCreateOpen,
    onOpen: onCreateOpen,
    onClose: onCreateClose,
  } = useDisclosure();

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<RuleFormValues>({
    resolver: zodResolver(ruleSchema),
    defaultValues: {
      trigger_type: 'after_due',
      days_offset: 3,
    },
  });

  const { data: rules, isLoading: rulesLoading } = useQuery({
    queryKey: ['reminder-rules'],
    queryFn: () => remindersService.listRules(),
  });

  const { data: logs, isLoading: logsLoading } = useQuery({
    queryKey: ['reminder-logs'],
    queryFn: () => remindersService.getLogs(),
  });

  const createMutation = useMutation({
    mutationFn: (data: RuleFormValues) => remindersService.createRule(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reminder-rules'] });
      toast({ title: 'Reminder rule created', status: 'success', duration: 3000, isClosable: true });
      reset();
      onCreateClose();
    },
    onError: () => {
      toast({ title: 'Failed to create rule', status: 'error', duration: 3000, isClosable: true });
    },
  });

  const toggleMutation = useMutation({
    mutationFn: ({ id, is_active }: { id: number; is_active: boolean }) =>
      remindersService.updateRule(id, { is_active }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reminder-rules'] });
    },
    onError: () => {
      toast({ title: 'Failed to update rule', status: 'error', duration: 3000, isClosable: true });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => remindersService.deleteRule(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reminder-rules'] });
      toast({ title: 'Rule deleted', status: 'success', duration: 3000, isClosable: true });
      setRuleToDelete(null);
      onDeleteClose();
    },
    onError: () => {
      toast({ title: 'Failed to delete rule', status: 'error', duration: 3000, isClosable: true });
    },
  });

  const handleDeleteClick = (rule: ReminderRule) => {
    setRuleToDelete(rule);
    onDeleteOpen();
  };

  const onSubmit = async (values: RuleFormValues) => {
    await createMutation.mutateAsync(values);
  };

  return (
    <PageWrapper>
      {/* Header */}
      <HStack justify="space-between" mb={8}>
        <HStack spacing={3}>
          <Bell size={24} color="#4F46E5" />
          <Heading size="lg" color="gray.800">Reminders</Heading>
        </HStack>
        <GradientButton leftIcon={<Plus size={16} />} onClick={onCreateOpen}>
          New Rule
        </GradientButton>
      </HStack>

      {/* Rules section */}
      <GlassCard p={0} overflow="hidden" mb={6}>
        <Box px={6} py={4} borderBottom="1px solid" borderColor="gray.100">
          <Heading size="sm" color="gray.700">Reminder Rules</Heading>
        </Box>

        {rulesLoading ? (
          <Center py={10}><Spinner size="lg" color="brand.500" /></Center>
        ) : !rules || rules.length === 0 ? (
          <Center py={10}>
            <VStack spacing={3}>
              <Bell size={36} color="#CBD5E0" />
              <Text color="gray.400" fontSize="sm">No reminder rules yet.</Text>
              <Button size="sm" colorScheme="brand" variant="outline" onClick={onCreateOpen}>
                Create your first rule
              </Button>
            </VStack>
          </Center>
        ) : (
          <TableContainer>
            <Table variant="simple">
              <Thead bg="gray.50">
                <Tr>
                  <Th fontSize="xs" textTransform="uppercase" color="gray.500">Name</Th>
                  <Th fontSize="xs" textTransform="uppercase" color="gray.500">Trigger</Th>
                  <Th fontSize="xs" textTransform="uppercase" color="gray.500" isNumeric>Days Offset</Th>
                  <Th fontSize="xs" textTransform="uppercase" color="gray.500">Status</Th>
                  <Th fontSize="xs" textTransform="uppercase" color="gray.500" isNumeric>Actions</Th>
                </Tr>
              </Thead>
              <Tbody>
                {rules.map((rule) => (
                  <Tr key={rule.id} _hover={{ bg: 'gray.50' }}>
                    <Td>
                      <Text fontSize="sm" fontWeight="600" color="gray.800">{rule.name}</Text>
                    </Td>
                    <Td>
                      <Badge
                        colorScheme={triggerColorScheme(rule.trigger_type)}
                        borderRadius="full"
                        px={3}
                        fontSize="xs"
                      >
                        {TRIGGER_LABELS[rule.trigger_type]}
                      </Badge>
                    </Td>
                    <Td isNumeric>
                      <Text fontSize="sm" color="gray.600">
                        {rule.days_offset === 0 ? '—' : `${rule.days_offset} day${rule.days_offset !== 1 ? 's' : ''}`}
                      </Text>
                    </Td>
                    <Td>
                      <HStack spacing={2}>
                        <Switch
                          isChecked={rule.is_active}
                          colorScheme="brand"
                          size="sm"
                          onChange={() =>
                            toggleMutation.mutate({ id: rule.id, is_active: !rule.is_active })
                          }
                          isDisabled={toggleMutation.isPending}
                        />
                        <Badge
                          colorScheme={rule.is_active ? 'green' : 'gray'}
                          borderRadius="full"
                          px={2}
                          fontSize="xs"
                        >
                          {rule.is_active ? 'Active' : 'Inactive'}
                        </Badge>
                      </HStack>
                    </Td>
                    <Td isNumeric>
                      <Tooltip label="Delete rule" hasArrow>
                        <IconButton
                          aria-label="Delete rule"
                          icon={<Trash2 size={15} />}
                          size="sm"
                          variant="ghost"
                          colorScheme="red"
                          onClick={() => handleDeleteClick(rule)}
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

      {/* Reminder Logs section */}
      <GlassCard p={0} overflow="hidden">
        <Box px={6} py={4} borderBottom="1px solid" borderColor="gray.100">
          <Heading size="sm" color="gray.700">Reminder Log</Heading>
        </Box>

        {logsLoading ? (
          <Center py={10}><Spinner size="lg" color="brand.500" /></Center>
        ) : !logs || logs.length === 0 ? (
          <Center py={10}>
            <Text color="gray.400" fontSize="sm">No reminders have been sent yet.</Text>
          </Center>
        ) : (
          <TableContainer>
            <Table variant="simple" size="sm">
              <Thead bg="gray.50">
                <Tr>
                  <Th fontSize="xs" textTransform="uppercase" color="gray.500">Sent At</Th>
                  <Th fontSize="xs" textTransform="uppercase" color="gray.500">Invoice</Th>
                  <Th fontSize="xs" textTransform="uppercase" color="gray.500">Email To</Th>
                  <Th fontSize="xs" textTransform="uppercase" color="gray.500">Status</Th>
                </Tr>
              </Thead>
              <Tbody>
                {logs.map((log) => (
                  <Tr key={log.id}>
                    <Td><Text fontSize="sm" color="gray.600">{formatDate(log.sent_at)}</Text></Td>
                    <Td><Text fontSize="sm" color="brand.500" fontWeight="500">#{log.invoice_id}</Text></Td>
                    <Td><Text fontSize="sm" color="gray.600">{log.email_to}</Text></Td>
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
        )}
      </GlassCard>

      {/* Create rule modal */}
      <Modal isOpen={isCreateOpen} onClose={onCreateClose} size="md">
        <ModalOverlay />
        <ModalContent borderRadius="xl">
          <ModalHeader color="gray.800">New Reminder Rule</ModalHeader>
          <ModalCloseButton />
          <form onSubmit={handleSubmit(onSubmit)} noValidate>
            <ModalBody>
              <VStack spacing={4}>
                <FormControl isInvalid={!!errors.name} isRequired>
                  <FormLabel fontSize="sm">Rule Name</FormLabel>
                  <Input
                    placeholder="e.g., 3-day follow-up"
                    {...register('name')}
                    focusBorderColor="brand.500"
                  />
                  <FormErrorMessage>{errors.name?.message}</FormErrorMessage>
                </FormControl>

                <FormControl isInvalid={!!errors.trigger_type} isRequired>
                  <FormLabel fontSize="sm">Trigger Type</FormLabel>
                  <Select {...register('trigger_type')} focusBorderColor="brand.500">
                    <option value="before_due">Before Due Date</option>
                    <option value="on_due">On Due Date</option>
                    <option value="after_due">After Due Date</option>
                  </Select>
                  <FormErrorMessage>{errors.trigger_type?.message}</FormErrorMessage>
                </FormControl>

                <FormControl isInvalid={!!errors.days_offset} isRequired>
                  <FormLabel fontSize="sm">Days Offset</FormLabel>
                  <Input
                    type="number"
                    min={0}
                    placeholder="3"
                    {...register('days_offset', { valueAsNumber: true })}
                    focusBorderColor="brand.500"
                  />
                  <Text fontSize="xs" color="gray.400" mt={1}>
                    Number of days before or after the due date. Use 0 for on-due reminders.
                  </Text>
                  <FormErrorMessage>{errors.days_offset?.message}</FormErrorMessage>
                </FormControl>
              </VStack>
            </ModalBody>
            <ModalFooter gap={3}>
              <Button variant="outline" onClick={onCreateClose}>Cancel</Button>
              <GradientButton
                type="submit"
                isLoading={isSubmitting || createMutation.isPending}
                loadingText="Creating..."
              >
                Create Rule
              </GradientButton>
            </ModalFooter>
          </form>
        </ModalContent>
      </Modal>

      {/* Delete confirm */}
      <AlertDialog isOpen={isDeleteOpen} leastDestructiveRef={cancelRef} onClose={onDeleteClose}>
        <AlertDialogOverlay>
          <AlertDialogContent borderRadius="xl">
            <AlertDialogHeader fontSize="lg" fontWeight="700" color="gray.800">
              Delete Rule
            </AlertDialogHeader>
            <AlertDialogBody color="gray.600">
              Are you sure you want to delete{' '}
              <Text as="span" fontWeight="700" color="gray.800">{ruleToDelete?.name}</Text>?
              This will stop future reminders from this rule.
            </AlertDialogBody>
            <AlertDialogFooter gap={3}>
              <Button ref={cancelRef} onClick={onDeleteClose} variant="outline">Cancel</Button>
              <Button
                colorScheme="red"
                onClick={() => ruleToDelete && deleteMutation.mutate(ruleToDelete.id)}
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

export default function RemindersPage() {
  return (
    <ProtectedRoute>
      <AppShell>
        <RemindersContent />
      </AppShell>
    </ProtectedRoute>
  );
}
