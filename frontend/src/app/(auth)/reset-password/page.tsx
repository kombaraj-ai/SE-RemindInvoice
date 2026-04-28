'use client';
import {
  Box,
  Center,
  VStack,
  Heading,
  Text,
  FormControl,
  FormLabel,
  Input,
  FormErrorMessage,
  Alert,
  AlertIcon,
  useToast,
} from '@chakra-ui/react';
import Link from 'next/link';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useRouter, useSearchParams } from 'next/navigation';
import { useState, Suspense } from 'react';
import { authService } from '@/services/auth';
import { GlassCard } from '@/components/ui/GlassCard';
import { GradientButton } from '@/components/ui/GradientButton';
import { PageWrapper } from '@/components/layout/PageWrapper';

const resetSchema = z
  .object({
    password: z.string().min(8, 'Password must be at least 8 characters'),
    confirm_password: z.string(),
  })
  .refine((data) => data.password === data.confirm_password, {
    message: 'Passwords do not match',
    path: ['confirm_password'],
  });

type ResetFormValues = z.infer<typeof resetSchema>;

function ResetPasswordForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const token = searchParams.get('token') ?? '';
  const toast = useToast();
  const [serverError, setServerError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<ResetFormValues>({
    resolver: zodResolver(resetSchema),
  });

  const onSubmit = async (values: ResetFormValues) => {
    if (!token) {
      setServerError('Invalid or missing reset token. Please request a new reset link.');
      return;
    }
    setServerError(null);
    try {
      await authService.resetPassword(token, values.password);
      toast({
        title: 'Password reset successful!',
        description: 'Your password has been updated. Please sign in with your new password.',
        status: 'success',
        duration: 5000,
        isClosable: true,
      });
      router.push('/login');
    } catch {
      setServerError('Failed to reset password. Your reset link may have expired.');
      toast({
        title: 'Reset failed',
        description: 'Your reset link may have expired. Please request a new one.',
        status: 'error',
        duration: 4000,
        isClosable: true,
      });
    }
  };

  return (
    <Center minH="100vh" bgGradient="linear(135deg, #eef2ff 0%, #ede9fe 50%, #f0fdf4 100%)">
      <PageWrapper w="full" maxW="420px" px={4}>
        <VStack spacing={8}>
          <Box textAlign="center">
            <Heading
              size="lg"
              bgGradient="linear(to-r, brand.500, brand.600)"
              bgClip="text"
              mb={2}
            >
              RemindInvoice
            </Heading>
            <Text color="gray.500" fontSize="sm">
              Set a new password
            </Text>
          </Box>

          <GlassCard w="full">
            <form onSubmit={handleSubmit(onSubmit)} noValidate>
              <VStack spacing={5}>
                {!token && (
                  <Alert status="warning" borderRadius="md">
                    <AlertIcon />
                    No reset token found. Please use the link from your email.
                  </Alert>
                )}

                {serverError && (
                  <Alert status="error" borderRadius="md">
                    <AlertIcon />
                    {serverError}
                  </Alert>
                )}

                <FormControl isInvalid={!!errors.password}>
                  <FormLabel fontSize="sm" fontWeight="500">
                    New Password
                  </FormLabel>
                  <Input
                    type="password"
                    placeholder="Min. 8 characters"
                    {...register('password')}
                    focusBorderColor="brand.500"
                    isDisabled={!token}
                  />
                  <FormErrorMessage>{errors.password?.message}</FormErrorMessage>
                </FormControl>

                <FormControl isInvalid={!!errors.confirm_password}>
                  <FormLabel fontSize="sm" fontWeight="500">
                    Confirm New Password
                  </FormLabel>
                  <Input
                    type="password"
                    placeholder="••••••••"
                    {...register('confirm_password')}
                    focusBorderColor="brand.500"
                    isDisabled={!token}
                  />
                  <FormErrorMessage>{errors.confirm_password?.message}</FormErrorMessage>
                </FormControl>

                <GradientButton
                  type="submit"
                  w="full"
                  isLoading={isSubmitting}
                  loadingText="Resetting..."
                  isDisabled={!token}
                >
                  Reset Password
                </GradientButton>
              </VStack>
            </form>
          </GlassCard>

          <Text fontSize="sm" color="gray.500">
            Remember your password?{' '}
            <Link href="/login" style={{ color: '#4F46E5', fontWeight: 600 }}>
              Sign in
            </Link>
          </Text>
        </VStack>
      </PageWrapper>
    </Center>
  );
}

export default function ResetPasswordPage() {
  return (
    <Suspense
      fallback={
        <Center minH="100vh" bgGradient="linear(135deg, #eef2ff 0%, #ede9fe 50%, #f0fdf4 100%)">
          <Text color="gray.500">Loading...</Text>
        </Center>
      }
    >
      <ResetPasswordForm />
    </Suspense>
  );
}
