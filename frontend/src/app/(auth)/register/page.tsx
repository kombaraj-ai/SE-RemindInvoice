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
  Divider,
  Button,
  useToast,
  HStack,
} from '@chakra-ui/react';
import Link from 'next/link';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useRouter } from 'next/navigation';
import { useState } from 'react';
import { authService } from '@/services/auth';
import { GlassCard } from '@/components/ui/GlassCard';
import { GradientButton } from '@/components/ui/GradientButton';
import { PageWrapper } from '@/components/layout/PageWrapper';

const registerSchema = z
  .object({
    full_name: z.string().min(2, 'Full name must be at least 2 characters'),
    email: z.string().email('Invalid email address'),
    password: z.string().min(8, 'Password must be at least 8 characters'),
    confirm_password: z.string(),
  })
  .refine((data) => data.password === data.confirm_password, {
    message: 'Passwords do not match',
    path: ['confirm_password'],
  });

type RegisterFormValues = z.infer<typeof registerSchema>;

export default function RegisterPage() {
  const router = useRouter();
  const toast = useToast();
  const [serverError, setServerError] = useState<string | null>(null);
  const [isGoogleLoading, setIsGoogleLoading] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<RegisterFormValues>({
    resolver: zodResolver(registerSchema),
  });

  const onSubmit = async (values: RegisterFormValues) => {
    setServerError(null);
    try {
      await authService.register({
        email: values.email,
        password: values.password,
        full_name: values.full_name,
      });
      toast({
        title: 'Account created!',
        description: 'Your account has been created successfully. Please sign in.',
        status: 'success',
        duration: 4000,
        isClosable: true,
      });
      router.push('/login');
    } catch {
      setServerError('Registration failed. This email may already be in use.');
      toast({
        title: 'Registration failed',
        description: 'This email may already be in use.',
        status: 'error',
        duration: 3000,
        isClosable: true,
      });
    }
  };

  const handleGoogleSignUp = () => {
    setIsGoogleLoading(true);
    const apiBase = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000/api/v1';
    window.location.href = `${apiBase}/auth/google`;
  };

  return (
    <Center minH="100vh" bgGradient="linear(135deg, #eef2ff 0%, #ede9fe 50%, #f0fdf4 100%)">
      <PageWrapper w="full" maxW="440px" px={4}>
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
              Create your free account
            </Text>
          </Box>

          <GlassCard w="full">
            <VStack spacing={5}>
              <Button
                w="full"
                variant="outline"
                borderColor="gray.300"
                color="gray.700"
                fontWeight="500"
                isLoading={isGoogleLoading}
                loadingText="Redirecting..."
                onClick={handleGoogleSignUp}
                leftIcon={
                  <Box as="span" w="18px" h="18px" display="inline-flex" alignItems="center">
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="18" height="18">
                      <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                      <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                      <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l3.66-2.84z"/>
                      <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                    </svg>
                  </Box>
                }
                _hover={{ borderColor: 'brand.300', bg: 'brand.50' }}
              >
                Sign up with Google
              </Button>

              <HStack w="full" align="center">
                <Divider />
                <Text fontSize="xs" color="gray.400" whiteSpace="nowrap" px={2}>
                  or continue with email
                </Text>
                <Divider />
              </HStack>

              <form onSubmit={handleSubmit(onSubmit)} noValidate style={{ width: '100%' }}>
                <VStack spacing={5}>
                  {serverError && (
                    <Alert status="error" borderRadius="md">
                      <AlertIcon />
                      {serverError}
                    </Alert>
                  )}

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

                  <FormControl isInvalid={!!errors.password}>
                    <FormLabel fontSize="sm" fontWeight="500">
                      Password
                    </FormLabel>
                    <Input
                      type="password"
                      placeholder="Min. 8 characters"
                      {...register('password')}
                      focusBorderColor="brand.500"
                    />
                    <FormErrorMessage>{errors.password?.message}</FormErrorMessage>
                  </FormControl>

                  <FormControl isInvalid={!!errors.confirm_password}>
                    <FormLabel fontSize="sm" fontWeight="500">
                      Confirm Password
                    </FormLabel>
                    <Input
                      type="password"
                      placeholder="••••••••"
                      {...register('confirm_password')}
                      focusBorderColor="brand.500"
                    />
                    <FormErrorMessage>{errors.confirm_password?.message}</FormErrorMessage>
                  </FormControl>

                  <GradientButton
                    type="submit"
                    w="full"
                    isLoading={isSubmitting}
                    loadingText="Creating account..."
                  >
                    Create Account
                  </GradientButton>
                </VStack>
              </form>
            </VStack>
          </GlassCard>

          <Text fontSize="sm" color="gray.500">
            Already have an account?{' '}
            <Link href="/login" style={{ color: '#4F46E5', fontWeight: 600 }}>
              Sign in
            </Link>
          </Text>
        </VStack>
      </PageWrapper>
    </Center>
  );
}
