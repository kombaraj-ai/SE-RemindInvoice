'use client';
import {
  Box,
  VStack,
  HStack,
  Heading,
  Text,
  FormControl,
  FormLabel,
  Input,
  Textarea,
  FormErrorMessage,
  Button,
  SimpleGrid,
  Divider,
  useToast,
  Select,
  Spinner,
  Center,
} from '@chakra-ui/react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useRouter } from 'next/navigation';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Edit, ArrowLeft } from 'lucide-react';
import { useEffect } from 'react';
import { clientsService } from '@/services/clients';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { AppShell } from '@/components/layout/AppShell';
import { GlassCard } from '@/components/ui/GlassCard';
import { GradientButton } from '@/components/ui/GradientButton';
import { PageWrapper } from '@/components/layout/PageWrapper';
import type { ClientUpdate } from '@/types/client';

const clientSchema = z.object({
  name: z.string().min(1, 'Name is required'),
  email: z.string().email('Invalid email address'),
  phone: z.string().optional(),
  company_name: z.string().optional(),
  address_line1: z.string().optional(),
  address_line2: z.string().optional(),
  city: z.string().optional(),
  state: z.string().optional(),
  postal_code: z.string().optional(),
  country: z.string().optional(),
  payment_terms_days: z
    .number({ invalid_type_error: 'Must be a number' })
    .int()
    .min(0, 'Must be 0 or more')
    .optional(),
  currency: z.string().optional(),
  notes: z.string().optional(),
});

type ClientFormValues = z.infer<typeof clientSchema>;

const CURRENCIES = ['INR', 'USD', 'EUR', 'GBP', 'CAD', 'AUD', 'JPY', 'SGD', 'CHF', 'MXN'];

const INDIAN_STATES = [
  'Andhra Pradesh',
  'Arunachal Pradesh',
  'Assam',
  'Bihar',
  'Chhattisgarh',
  'Goa',
  'Gujarat',
  'Haryana',
  'Himachal Pradesh',
  'Jharkhand',
  'Karnataka',
  'Kerala',
  'Madhya Pradesh',
  'Maharashtra',
  'Manipur',
  'Meghalaya',
  'Mizoram',
  'Nagaland',
  'Odisha',
  'Punjab',
  'Rajasthan',
  'Sikkim',
  'Tamil Nadu',
  'Telangana',
  'Tripura',
  'Uttar Pradesh',
  'Uttarakhand',
  'West Bengal',
  'Andaman and Nicobar Islands',
  'Chandigarh',
  'Dadra and Nagar Haveli and Daman and Diu',
  'Delhi (NCT)',
  'Jammu and Kashmir',
  'Ladakh',
  'Lakshadweep',
  'Puducherry',
];

const COUNTRIES = [
  'India',
  'United States',
  'United Kingdom',
  'Canada',
  'Australia',
  'Singapore',
  'UAE',
  'Germany',
  'France',
  'Japan',
  'Other',
];

function EditClientContent({ id }: { id: number }) {
  const router = useRouter();
  const toast = useToast();
  const queryClient = useQueryClient();

  const { data: client, isLoading, isError } = useQuery({
    queryKey: ['client', id],
    queryFn: () => clientsService.get(id),
  });

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<ClientFormValues>({
    resolver: zodResolver(clientSchema),
  });

  useEffect(() => {
    if (client) {
      reset({
        name: client.name,
        email: client.email,
        phone: client.phone ?? '',
        company_name: client.company_name ?? '',
        address_line1: client.address_line1 ?? '',
        address_line2: client.address_line2 ?? '',
        city: client.city ?? '',
        state: client.state ?? '',
        postal_code: client.postal_code ?? '',
        country: client.country ?? 'India',
        payment_terms_days: client.payment_terms_days,
        currency: client.currency,
        notes: client.notes ?? '',
      });
    }
  }, [client, reset]);

  const updateMutation = useMutation({
    mutationFn: (data: ClientUpdate) => clientsService.update(id, data),
    onSuccess: (updated) => {
      queryClient.invalidateQueries({ queryKey: ['client', id] });
      queryClient.invalidateQueries({ queryKey: ['clients'] });
      toast({
        title: 'Client updated',
        description: `${updated.name} has been saved.`,
        status: 'success',
        duration: 3000,
        isClosable: true,
      });
      router.push(`/clients/${id}`);
    },
    onError: () => {
      toast({
        title: 'Update failed',
        description: 'Something went wrong. Please try again.',
        status: 'error',
        duration: 3000,
        isClosable: true,
      });
    },
  });

  const onSubmit = async (values: ClientFormValues) => {
    const payload: ClientUpdate = {
      name: values.name,
      email: values.email,
      phone: values.phone || undefined,
      company_name: values.company_name || undefined,
      address_line1: values.address_line1 || undefined,
      city: values.city || undefined,
      country: values.country || undefined,
      payment_terms_days: values.payment_terms_days,
      currency: values.currency,
      notes: values.notes || undefined,
    };
    await updateMutation.mutateAsync(payload);
  };

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

  return (
    <PageWrapper>
      <HStack spacing={3} mb={8}>
        <Button
          variant="ghost"
          leftIcon={<ArrowLeft size={16} />}
          color="gray.600"
          onClick={() => router.push(`/clients/${id}`)}
          size="sm"
        >
          Back to {client.name}
        </Button>
      </HStack>

      <HStack spacing={3} mb={6}>
        <Edit size={24} color="#4F46E5" />
        <Heading size="lg" color="gray.800">
          Edit Client
        </Heading>
      </HStack>

      <GlassCard maxW="760px">
        <form onSubmit={handleSubmit(onSubmit)} noValidate>
          <VStack spacing={6} align="stretch">
            {/* Basic info */}
            <Box>
              <Text fontSize="sm" fontWeight="600" color="brand.500" mb={4} textTransform="uppercase" letterSpacing="wide">
                Basic Information
              </Text>
              <SimpleGrid columns={{ base: 1, md: 2 }} spacing={4}>
                <FormControl isInvalid={!!errors.name} isRequired>
                  <FormLabel fontSize="sm" fontWeight="500">Full Name</FormLabel>
                  <Input placeholder="Rajesh Kumar" {...register('name')} focusBorderColor="brand.500" />
                  <FormErrorMessage>{errors.name?.message}</FormErrorMessage>
                </FormControl>

                <FormControl isInvalid={!!errors.email} isRequired>
                  <FormLabel fontSize="sm" fontWeight="500">Email</FormLabel>
                  <Input
                    type="email"
                    placeholder="rajesh@example.com"
                    {...register('email')}
                    focusBorderColor="brand.500"
                  />
                  <FormErrorMessage>{errors.email?.message}</FormErrorMessage>
                </FormControl>

                <FormControl isInvalid={!!errors.phone}>
                  <FormLabel fontSize="sm" fontWeight="500">Phone</FormLabel>
                  <Input type="tel" placeholder="+91 98765 43210" {...register('phone')} focusBorderColor="brand.500" />
                  <FormErrorMessage>{errors.phone?.message}</FormErrorMessage>
                </FormControl>

                <FormControl isInvalid={!!errors.company_name}>
                  <FormLabel fontSize="sm" fontWeight="500">Company Name</FormLabel>
                  <Input placeholder="Infosys Ltd." {...register('company_name')} focusBorderColor="brand.500" />
                  <FormErrorMessage>{errors.company_name?.message}</FormErrorMessage>
                </FormControl>
              </SimpleGrid>
            </Box>

            <Divider />

            {/* Address */}
            <Box>
              <Text fontSize="sm" fontWeight="600" color="brand.500" mb={4} textTransform="uppercase" letterSpacing="wide">
                Address
              </Text>
              <VStack spacing={4}>
                <FormControl isInvalid={!!errors.address_line1}>
                  <FormLabel fontSize="sm" fontWeight="500">Address Line 1</FormLabel>
                  <Input placeholder="42, Anna Salai" {...register('address_line1')} focusBorderColor="brand.500" />
                  <FormErrorMessage>{errors.address_line1?.message}</FormErrorMessage>
                </FormControl>

                <FormControl isInvalid={!!errors.address_line2}>
                  <FormLabel fontSize="sm" fontWeight="500">Address Line 2</FormLabel>
                  <Input placeholder="Flat No. 5, 2nd Floor" {...register('address_line2')} focusBorderColor="brand.500" />
                  <FormErrorMessage>{errors.address_line2?.message}</FormErrorMessage>
                </FormControl>

                <SimpleGrid columns={{ base: 1, md: 2 }} spacing={4} w="full">
                  <FormControl isInvalid={!!errors.city}>
                    <FormLabel fontSize="sm" fontWeight="500">City</FormLabel>
                    <Input placeholder="Chennai" {...register('city')} focusBorderColor="brand.500" />
                    <FormErrorMessage>{errors.city?.message}</FormErrorMessage>
                  </FormControl>

                  <FormControl isInvalid={!!errors.state}>
                    <FormLabel fontSize="sm" fontWeight="500">State / UT</FormLabel>
                    <Select
                      placeholder="Select state"
                      {...register('state')}
                      focusBorderColor="brand.500"
                    >
                      {INDIAN_STATES.map((s) => (
                        <option key={s} value={s}>{s}</option>
                      ))}
                    </Select>
                    <FormErrorMessage>{errors.state?.message}</FormErrorMessage>
                  </FormControl>

                  <FormControl isInvalid={!!errors.postal_code}>
                    <FormLabel fontSize="sm" fontWeight="500">PIN Code</FormLabel>
                    <Input placeholder="600001" {...register('postal_code')} focusBorderColor="brand.500" />
                    <FormErrorMessage>{errors.postal_code?.message}</FormErrorMessage>
                  </FormControl>

                  <FormControl isInvalid={!!errors.country}>
                    <FormLabel fontSize="sm" fontWeight="500">Country</FormLabel>
                    <Select {...register('country')} focusBorderColor="brand.500">
                      {COUNTRIES.map((c) => (
                        <option key={c} value={c}>{c}</option>
                      ))}
                    </Select>
                    <FormErrorMessage>{errors.country?.message}</FormErrorMessage>
                  </FormControl>
                </SimpleGrid>
              </VStack>
            </Box>

            <Divider />

            {/* Billing */}
            <Box>
              <Text fontSize="sm" fontWeight="600" color="brand.500" mb={4} textTransform="uppercase" letterSpacing="wide">
                Billing Settings
              </Text>
              <SimpleGrid columns={{ base: 1, md: 2 }} spacing={4}>
                <FormControl isInvalid={!!errors.payment_terms_days}>
                  <FormLabel fontSize="sm" fontWeight="500">Payment Terms (days)</FormLabel>
                  <Input
                    type="number"
                    min={0}
                    placeholder="30"
                    {...register('payment_terms_days', { valueAsNumber: true })}
                    focusBorderColor="brand.500"
                  />
                  <FormErrorMessage>{errors.payment_terms_days?.message}</FormErrorMessage>
                </FormControl>

                <FormControl isInvalid={!!errors.currency}>
                  <FormLabel fontSize="sm" fontWeight="500">Currency</FormLabel>
                  <Select {...register('currency')} focusBorderColor="brand.500">
                    {CURRENCIES.map((c) => (
                      <option key={c} value={c}>{c}</option>
                    ))}
                  </Select>
                  <FormErrorMessage>{errors.currency?.message}</FormErrorMessage>
                </FormControl>
              </SimpleGrid>
            </Box>

            <Divider />

            {/* Notes */}
            <FormControl isInvalid={!!errors.notes}>
              <FormLabel fontSize="sm" fontWeight="500">Notes</FormLabel>
              <Textarea
                placeholder="Any additional notes about this client..."
                rows={3}
                {...register('notes')}
                focusBorderColor="brand.500"
                resize="vertical"
              />
              <FormErrorMessage>{errors.notes?.message}</FormErrorMessage>
            </FormControl>

            {/* Actions */}
            <HStack spacing={3} pt={2}>
              <GradientButton
                type="submit"
                isLoading={isSubmitting || updateMutation.isPending}
                loadingText="Saving..."
              >
                Save Changes
              </GradientButton>
              <Button variant="outline" onClick={() => router.push(`/clients/${id}`)}>
                Cancel
              </Button>
            </HStack>
          </VStack>
        </form>
      </GlassCard>
    </PageWrapper>
  );
}

export default function EditClientPage({ params }: { params: { id: string } }) {
  return (
    <ProtectedRoute>
      <AppShell>
        <EditClientContent id={Number(params.id)} />
      </AppShell>
    </ProtectedRoute>
  );
}
