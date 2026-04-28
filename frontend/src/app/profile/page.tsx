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
  FormErrorMessage,
  FormHelperText,
  Avatar,
  Badge,
  Divider,
  useToast,
  Spinner,
  Center,
} from '@chakra-ui/react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useEffect } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { User } from 'lucide-react';
import { authService } from '@/services/auth';
import { useAuth } from '@/context/AuthContext';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { AppShell } from '@/components/layout/AppShell';
import { GlassCard } from '@/components/ui/GlassCard';
import { GradientButton } from '@/components/ui/GradientButton';
import { PageWrapper } from '@/components/layout/PageWrapper';

const profileSchema = z.object({
  full_name: z.string().min(1, 'Full name is required'),
  email: z.string().email('Invalid email address'),
  avatar_url: z.string().url('Must be a valid URL').optional().or(z.literal('')),
});

type ProfileFormValues = z.infer<typeof profileSchema>;

function ProfileContent() {
  const { user, refreshUser } = useAuth();
  const toast = useToast();
  const queryClient = useQueryClient();

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting, isDirty },
  } = useForm<ProfileFormValues>({
    resolver: zodResolver(profileSchema),
    defaultValues: {
      full_name: '',
      email: '',
      avatar_url: '',
    },
  });

  useEffect(() => {
    if (user) {
      reset({
        full_name: user.full_name ?? '',
        email: user.email,
        avatar_url: user.avatar_url ?? '',
      });
    }
  }, [user, reset]);

  const updateMutation = useMutation({
    mutationFn: (data: ProfileFormValues) =>
      authService.updateProfile({
        full_name: data.full_name,
        email: data.email,
        avatar_url: data.avatar_url || undefined,
      }),
    onSuccess: async () => {
      await refreshUser();
      await queryClient.invalidateQueries({ queryKey: ['me'] });
      toast({
        title: 'Profile updated',
        description: 'Your profile has been saved successfully.',
        status: 'success',
        duration: 3000,
        isClosable: true,
      });
    },
    onError: () => {
      toast({
        title: 'Update failed',
        description: 'Could not save your profile. Please try again.',
        status: 'error',
        duration: 3000,
        isClosable: true,
      });
    },
  });

  const onSubmit = async (values: ProfileFormValues) => {
    await updateMutation.mutateAsync(values);
  };

  if (!user) {
    return (
      <Center h="200px">
        <Spinner size="xl" color="brand.500" />
      </Center>
    );
  }

  const initials = user.full_name
    ? user.full_name
        .split(' ')
        .map((n) => n[0])
        .join('')
        .toUpperCase()
        .slice(0, 2)
    : user.email.slice(0, 2).toUpperCase();

  return (
    <PageWrapper>
      <HStack spacing={3} mb={8}>
        <User size={24} color="#4F46E5" />
        <Heading size="lg" color="gray.800">
          My Profile
        </Heading>
      </HStack>

      <VStack spacing={6} align="stretch" maxW="640px">
        {/* Avatar section */}
        <GlassCard>
          <HStack spacing={6} align="center">
            <Avatar
              size="xl"
              name={user.full_name ?? user.email}
              src={user.avatar_url ?? undefined}
              bg="brand.500"
              color="white"
              fontSize="xl"
              fontWeight="700"
            >
              {!user.avatar_url && (
                <Box
                  position="absolute"
                  inset={0}
                  display="flex"
                  alignItems="center"
                  justifyContent="center"
                  fontWeight="700"
                  fontSize="xl"
                  color="white"
                >
                  {initials}
                </Box>
              )}
            </Avatar>
            <VStack align="start" spacing={1}>
              <Text fontWeight="700" fontSize="lg" color="gray.800">
                {user.full_name ?? 'No name set'}
              </Text>
              <Text fontSize="sm" color="gray.500">
                {user.email}
              </Text>
              <HStack spacing={2} mt={1}>
                {user.is_verified && (
                  <Badge colorScheme="green" borderRadius="full" px={2} fontSize="xs">
                    Verified
                  </Badge>
                )}
                {user.is_admin && (
                  <Badge colorScheme="purple" borderRadius="full" px={2} fontSize="xs">
                    Admin
                  </Badge>
                )}
                {user.oauth_provider && (
                  <Badge colorScheme="blue" borderRadius="full" px={2} fontSize="xs">
                    {user.oauth_provider}
                  </Badge>
                )}
              </HStack>
            </VStack>
          </HStack>
        </GlassCard>

        {/* Edit form */}
        <GlassCard>
          <Heading size="sm" color="gray.700" mb={5}>
            Edit Profile
          </Heading>
          <Divider mb={5} />

          <form onSubmit={handleSubmit(onSubmit)} noValidate>
            <VStack spacing={5}>
              <FormControl isInvalid={!!errors.full_name}>
                <FormLabel fontSize="sm" fontWeight="500">
                  Full Name
                </FormLabel>
                <Input
                  placeholder="Jane Smith"
                  {...register('full_name')}
                  focusBorderColor="brand.500"
                />
                <FormErrorMessage>{errors.full_name?.message}</FormErrorMessage>
              </FormControl>

              <FormControl isInvalid={!!errors.email} isRequired>
                <FormLabel fontSize="sm" fontWeight="500">
                  Email
                </FormLabel>
                <Input
                  type="email"
                  placeholder="you@example.com"
                  {...register('email')}
                  focusBorderColor="brand.500"
                />
                <FormErrorMessage>{errors.email?.message}</FormErrorMessage>
              </FormControl>

              <FormControl isInvalid={!!errors.avatar_url}>
                <FormLabel fontSize="sm" fontWeight="500">
                  Avatar URL
                </FormLabel>
                <Input
                  type="url"
                  placeholder="https://example.com/avatar.jpg"
                  {...register('avatar_url')}
                  focusBorderColor="brand.500"
                />
                <FormErrorMessage>{errors.avatar_url?.message}</FormErrorMessage>
                <Text fontSize="xs" color="gray.400" mt={1}>
                  Enter a URL for your profile picture.
                </Text>
              </FormControl>

              <Box w="full" pt={2}>
                <GradientButton
                  type="submit"
                  isLoading={isSubmitting || updateMutation.isPending}
                  loadingText="Saving..."
                  isDisabled={!isDirty}
                >
                  Save Changes
                </GradientButton>
              </Box>
            </VStack>
          </form>
        </GlassCard>

        {/* Account info */}
        <GlassCard>
          <Heading size="sm" color="gray.700" mb={4}>
            Account Information
          </Heading>
          <Divider mb={4} />
          <VStack spacing={3} align="stretch">
            <HStack justify="space-between">
              <Text fontSize="sm" color="gray.500">
                Member since
              </Text>
              <Text fontSize="sm" fontWeight="500" color="gray.800">
                {new Date(user.created_at).toLocaleDateString('en-US', {
                  year: 'numeric',
                  month: 'long',
                  day: 'numeric',
                })}
              </Text>
            </HStack>
            <HStack justify="space-between">
              <Text fontSize="sm" color="gray.500">
                Account status
              </Text>
              <Badge colorScheme={user.is_active ? 'green' : 'red'} borderRadius="full" px={2}>
                {user.is_active ? 'Active' : 'Inactive'}
              </Badge>
            </HStack>
            {user.oauth_provider && (
              <HStack justify="space-between">
                <Text fontSize="sm" color="gray.500">
                  Signed in with
                </Text>
                <Text fontSize="sm" fontWeight="500" color="gray.800" textTransform="capitalize">
                  {user.oauth_provider}
                </Text>
              </HStack>
            )}
          </VStack>
        </GlassCard>
      </VStack>
    </PageWrapper>
  );
}

export default function ProfilePage() {
  return (
    <ProtectedRoute>
      <AppShell>
        <ProfileContent />
      </AppShell>
    </ProtectedRoute>
  );
}
