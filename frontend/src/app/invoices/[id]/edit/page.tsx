'use client';
import {
  Heading,
  HStack,
  VStack,
  FormControl,
  FormLabel,
  FormErrorMessage,
  Input,
  Textarea,
  Select,
  NumberInput,
  NumberInputField,
  NumberInputStepper,
  NumberIncrementStepper,
  NumberDecrementStepper,
  Button,
  Text,
  Divider,
  Box,
  Spinner,
  Center,
  useToast,
  SimpleGrid,
  Alert,
  AlertIcon,
  AlertTitle,
  AlertDescription,
} from '@chakra-ui/react';
import { ArrowLeft, Edit } from 'lucide-react';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useRouter } from 'next/navigation';
import { useState, useEffect } from 'react';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { AppShell } from '@/components/layout/AppShell';
import { GlassCard } from '@/components/ui/GlassCard';
import { GradientButton } from '@/components/ui/GradientButton';
import { PageWrapper } from '@/components/layout/PageWrapper';
import { LineItemsEditor } from '@/components/invoices/LineItemsEditor';
import { invoicesService } from '@/services/invoices';
import { clientsService } from '@/services/clients';
import type { InvoiceCreate } from '@/types/invoice';

const schema = z.object({
  client_id: z.string().min(1, 'Client is required'),
  issue_date: z.string().min(1, 'Issue date is required'),
  due_date: z.string().min(1, 'Due date is required'),
  tax_rate: z.number().min(0).max(100),
  discount_amount: z.number().min(0),
  currency: z.string().min(1),
  notes: z.string().optional(),
});

type FormValues = z.infer<typeof schema>;

interface LineItemState {
  description: string;
  quantity: number;
  unit_price: number;
  sort_order: number;
}

function EditInvoiceContent({ id }: { id: number }) {
  const router = useRouter();
  const toast = useToast();
  const queryClient = useQueryClient();
  const [lineItems, setLineItems] = useState<LineItemState[]>([]);

  const { data: invoice, isLoading, isError } = useQuery({
    queryKey: ['invoice', id],
    queryFn: () => invoicesService.get(id),
  });

  const { data: clientsData, isLoading: clientsLoading } = useQuery({
    queryKey: ['clients'],
    queryFn: () => clientsService.list({ active_only: true, limit: 200 }),
  });

  const {
    register,
    handleSubmit,
    control,
    watch,
    reset,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      tax_rate: 0,
      discount_amount: 0,
      currency: 'INR',
    },
  });

  useEffect(() => {
    if (invoice) {
      reset({
        client_id: String(invoice.client_id),
        issue_date: invoice.issue_date,
        due_date: invoice.due_date,
        tax_rate: invoice.tax_rate,
        discount_amount: invoice.discount_amount,
        currency: invoice.currency,
        notes: invoice.notes ?? '',
      });
      if (invoice.items && invoice.items.length > 0) {
        setLineItems(
          invoice.items.map((item) => ({
            description: item.description,
            quantity: item.quantity,
            unit_price: item.unit_price,
            sort_order: item.sort_order,
          }))
        );
      } else {
        setLineItems([{ description: '', quantity: 1, unit_price: 0, sort_order: 0 }]);
      }
    }
  }, [invoice, reset]);

  const updateMutation = useMutation({
    mutationFn: (data: Partial<InvoiceCreate>) => invoicesService.update(id, data),
    onSuccess: (updated) => {
      queryClient.invalidateQueries({ queryKey: ['invoice', id] });
      queryClient.invalidateQueries({ queryKey: ['invoices'] });
      toast({
        title: 'Invoice updated',
        description: `${updated.invoice_number} has been saved.`,
        status: 'success',
        duration: 3000,
        isClosable: true,
      });
      router.push(`/invoices/${id}`);
    },
    onError: () => {
      toast({
        title: 'Failed to update invoice',
        status: 'error',
        duration: 3000,
        isClosable: true,
      });
    },
  });

  const taxRate = watch('tax_rate') ?? 0;
  const discountAmount = watch('discount_amount') ?? 0;
  const subtotal = lineItems.reduce((sum, item) => sum + item.quantity * item.unit_price, 0);
  const taxAmount = subtotal * (taxRate / 100);
  const total = subtotal + taxAmount - discountAmount;

  const onSubmit = (values: FormValues) => {
    const payload: Partial<InvoiceCreate> = {
      client_id: parseInt(values.client_id, 10),
      issue_date: values.issue_date,
      due_date: values.due_date,
      tax_rate: values.tax_rate,
      discount_amount: values.discount_amount,
      currency: values.currency,
      notes: values.notes,
      items: lineItems.map((item) => ({
        description: item.description,
        quantity: item.quantity,
        unit_price: item.unit_price,
        sort_order: item.sort_order,
      })),
    };
    updateMutation.mutate(payload);
  };

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

  if (invoice.status !== 'draft') {
    return (
      <PageWrapper>
        <HStack spacing={3} mb={8}>
          <Button
            leftIcon={<ArrowLeft size={16} />}
            variant="ghost"
            size="sm"
            onClick={() => router.push(`/invoices/${id}`)}
            color="gray.600"
          >
            Back to Invoice
          </Button>
        </HStack>
        <Alert
          status="warning"
          borderRadius="xl"
          flexDirection="column"
          alignItems="flex-start"
          gap={2}
          p={6}
        >
          <HStack>
            <AlertIcon />
            <AlertTitle>Read-only Invoice</AlertTitle>
          </HStack>
          <AlertDescription>
            Only draft invoices can be edited. This invoice has status{' '}
            <Text as="span" fontWeight="700" textTransform="capitalize">
              {invoice.status}
            </Text>{' '}
            and cannot be modified. You can duplicate it to create an editable copy.
          </AlertDescription>
          <HStack mt={2} spacing={3}>
            <Button
              colorScheme="brand"
              variant="outline"
              size="sm"
              onClick={() => router.push(`/invoices/${id}`)}
            >
              View Invoice
            </Button>
          </HStack>
        </Alert>
      </PageWrapper>
    );
  }

  return (
    <PageWrapper>
      <HStack spacing={3} mb={8}>
        <Button
          leftIcon={<ArrowLeft size={16} />}
          variant="ghost"
          size="sm"
          onClick={() => router.push(`/invoices/${id}`)}
          color="gray.600"
        >
          Back
        </Button>
        <Edit size={24} color="#4F46E5" />
        <Heading size="lg" color="gray.800">
          Edit Invoice
        </Heading>
        <Text fontSize="sm" color="gray.500">({invoice.invoice_number})</Text>
      </HStack>

      <form onSubmit={handleSubmit(onSubmit)}>
        <VStack spacing={6} align="stretch">
          <GlassCard>
            <Heading size="sm" color="gray.700" mb={4}>
              Invoice Details
            </Heading>
            <SimpleGrid columns={{ base: 1, md: 2 }} spacing={4}>
              <FormControl isInvalid={!!errors.client_id}>
                <FormLabel fontSize="sm" color="gray.600">Client</FormLabel>
                {clientsLoading ? (
                  <Center h="40px"><Spinner size="sm" color="brand.500" /></Center>
                ) : (
                  <Select {...register('client_id')} placeholder="Select a client" focusBorderColor="brand.500">
                    {clientsData?.items.map((client) => (
                      <option key={client.id} value={client.id}>
                        {client.name}{client.company_name ? ` — ${client.company_name}` : ''}
                      </option>
                    ))}
                  </Select>
                )}
                <FormErrorMessage>{errors.client_id?.message}</FormErrorMessage>
              </FormControl>

              <FormControl isInvalid={!!errors.currency}>
                <FormLabel fontSize="sm" color="gray.600">Currency</FormLabel>
                <Select {...register('currency')} focusBorderColor="brand.500">
                  <option value="INR">INR — Indian Rupee</option>
                  <option value="USD">USD — US Dollar</option>
                  <option value="EUR">EUR — Euro</option>
                  <option value="GBP">GBP — British Pound</option>
                  <option value="CAD">CAD — Canadian Dollar</option>
                  <option value="AUD">AUD — Australian Dollar</option>
                </Select>
              </FormControl>

              <FormControl isInvalid={!!errors.issue_date}>
                <FormLabel fontSize="sm" color="gray.600">Issue Date</FormLabel>
                <Input type="date" {...register('issue_date')} focusBorderColor="brand.500" />
                <FormErrorMessage>{errors.issue_date?.message}</FormErrorMessage>
              </FormControl>

              <FormControl isInvalid={!!errors.due_date}>
                <FormLabel fontSize="sm" color="gray.600">Due Date</FormLabel>
                <Input type="date" {...register('due_date')} focusBorderColor="brand.500" />
                <FormErrorMessage>{errors.due_date?.message}</FormErrorMessage>
              </FormControl>
            </SimpleGrid>
          </GlassCard>

          <GlassCard p={0} overflow="hidden">
            <Box px={6} pt={6} pb={4}>
              <Heading size="sm" color="gray.700">Line Items</Heading>
            </Box>
            <LineItemsEditor items={lineItems} onChange={setLineItems} />
          </GlassCard>

          <GlassCard>
            <Heading size="sm" color="gray.700" mb={4}>Charges & Notes</Heading>
            <SimpleGrid columns={{ base: 1, md: 2 }} spacing={4}>
              <FormControl>
                <FormLabel fontSize="sm" color="gray.600">Tax Rate (%)</FormLabel>
                <Controller
                  name="tax_rate"
                  control={control}
                  render={({ field }) => (
                    <NumberInput
                      {...field}
                      min={0}
                      max={100}
                      step={0.5}
                      onChange={(_, val) => field.onChange(isNaN(val) ? 0 : val)}
                      focusBorderColor="brand.500"
                    >
                      <NumberInputField />
                      <NumberInputStepper>
                        <NumberIncrementStepper />
                        <NumberDecrementStepper />
                      </NumberInputStepper>
                    </NumberInput>
                  )}
                />
              </FormControl>

              <FormControl>
                <FormLabel fontSize="sm" color="gray.600">Discount Amount</FormLabel>
                <Controller
                  name="discount_amount"
                  control={control}
                  render={({ field }) => (
                    <NumberInput
                      {...field}
                      min={0}
                      step={0.01}
                      onChange={(_, val) => field.onChange(isNaN(val) ? 0 : val)}
                      focusBorderColor="brand.500"
                    >
                      <NumberInputField />
                      <NumberInputStepper>
                        <NumberIncrementStepper />
                        <NumberDecrementStepper />
                      </NumberInputStepper>
                    </NumberInput>
                  )}
                />
              </FormControl>

              <FormControl gridColumn={{ md: 'span 2' }}>
                <FormLabel fontSize="sm" color="gray.600">Notes</FormLabel>
                <Textarea
                  {...register('notes')}
                  placeholder="Payment terms, bank details, or any other notes..."
                  rows={3}
                  focusBorderColor="brand.500"
                  resize="vertical"
                />
              </FormControl>
            </SimpleGrid>

            <Divider my={4} />

            <VStack align="flex-end" spacing={2}>
              <HStack justify="space-between" w="260px">
                <Text fontSize="sm" color="gray.500">Subtotal:</Text>
                <Text fontSize="sm" color="gray.700">₹{subtotal.toFixed(2)}</Text>
              </HStack>
              <HStack justify="space-between" w="260px">
                <Text fontSize="sm" color="gray.500">Tax ({taxRate}%):</Text>
                <Text fontSize="sm" color="gray.700">₹{taxAmount.toFixed(2)}</Text>
              </HStack>
              <HStack justify="space-between" w="260px">
                <Text fontSize="sm" color="gray.500">Discount:</Text>
                <Text fontSize="sm" color="red.500">-₹{Number(discountAmount).toFixed(2)}</Text>
              </HStack>
              <Divider w="260px" />
              <HStack justify="space-between" w="260px">
                <Text fontSize="md" fontWeight="700" color="gray.800">Total:</Text>
                <Text fontSize="md" fontWeight="700" color="brand.500">₹{total.toFixed(2)}</Text>
              </HStack>
            </VStack>
          </GlassCard>

          <HStack justify="flex-end" spacing={3}>
            <Button variant="ghost" onClick={() => router.push(`/invoices/${id}`)} color="gray.600">
              Cancel
            </Button>
            <GradientButton
              type="submit"
              isLoading={updateMutation.isPending}
              loadingText="Saving..."
            >
              Save Changes
            </GradientButton>
          </HStack>
        </VStack>
      </form>
    </PageWrapper>
  );
}

export default function EditInvoicePage({ params }: { params: { id: string } }) {
  return (
    <ProtectedRoute>
      <AppShell>
        <EditInvoiceContent id={Number(params.id)} />
      </AppShell>
    </ProtectedRoute>
  );
}
