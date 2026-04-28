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
  Icon,
} from '@chakra-ui/react';
import Link from 'next/link';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useState } from 'react';
import { CheckCircle } from 'lucide-react';
import { authService } from '@/services/auth';
import { GlassCard } from '@/components/ui/GlassCard';
import { GradientButton } from '@/components/ui/GradientButton';
import { PageWrapper } from '@/components/layout/PageWrapper';

const forgotSchema = z.object({
  email: z.string().email('Invalid email address'),
});

type ForgotFormValues = z.infer<typeof forgotSchema>;

export default function ForgotPasswordPage() {
  const toast = useToast();
  const [submitted, setSubmitted] = useState(false);
  const [serverError, setServerError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<ForgotFormValues>({
    resolver: zodResolver(forgotSchema),
  });

  const onSubmit = async (values: ForgotFormValues) => {
    setServerError(null);
    try {
      await authService.forgotPassword(values.email);
      setSubmitted(true);
    } catch {
      setServerError('Something went wrong. Please try again.');
      toast({
        title: 'Request failed',
        description: 'Could not send reset email. Please try again.',
        status: 'error',
        duration: 3000,
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
              Reset your password
            </Text>
          </Box>

          <GlassCard w="full">
            {submitted ? (
              <VStack spacing={4} py={4} textAlign="center">
                <Icon as={CheckCircle} boxSize={12} color="green.500" />
                <Heading size="md" color="gray.800">
                  Check your email
                </Heading>
                <Text color="gray.600" fontSize="sm">
                  We sent a password reset link to your email address. Please check your inbox and
                  follow the instructions.
                </Text>
                <Text fontSize="sm" color="gray.500">
                  Didn&apos;t receive it?{' '}
                  <Box
                    as="button"
                    color="brand.500"
                    fontWeight="600"
                    onClick={() => setSubmitted(false)}
                    _hover={{ textDecoration: 'underline' }}
                  >
                    Try again
                  </Box>
                </Text>
              </VStack>
            ) : (
              <form onSubmit={handleSubmit(onSubmit)} noValidate>
                <VStack spacing={5}>
                  {serverError && (
                    <Alert status="error" borderRadius="md">
                      <AlertIcon />
                      {serverError}
                    </Alert>
                  )}

                  <Text fontSize="sm" color="gray.600" textAlign="center">
                    Enter your email address and we&apos;ll send you a link to reset your password.
                  </Text>

                  <FormControl isInvalid={!!errors.email}>
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

                  <GradientButton
                    type="submit"
                    w="full"
                    isLoading={isSubmitting}
                    loadingText="Sending..."
                  >
                    Send Reset Link
                  </GradientButton>
                </VStack>
              </form>
            )}
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
