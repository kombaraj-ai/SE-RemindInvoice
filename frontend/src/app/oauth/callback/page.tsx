'use client';
import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Center, Spinner, Text, VStack } from '@chakra-ui/react';

export default function OAuthCallbackPage() {
  const router = useRouter();

  useEffect(() => {
    const hash = window.location.hash.slice(1);
    const params = new URLSearchParams(hash);

    const accessToken = params.get('access_token');
    const refreshToken = params.get('refresh_token');
    const error = params.get('error');

    // Clear the fragment from the address bar immediately
    window.history.replaceState(null, '', window.location.pathname);

    if (error || !accessToken || !refreshToken) {
      router.replace('/login?error=oauth_failed');
      return;
    }

    localStorage.setItem('access_token', accessToken);
    localStorage.setItem('refresh_token', refreshToken);
    router.replace('/dashboard');
  }, [router]);

  return (
    <Center minH="100vh" bg="gray.50">
      <VStack spacing={4}>
        <Spinner size="xl" color="brand.500" thickness="4px" />
        <Text color="gray.500" fontSize="sm">
          Completing sign-in...
        </Text>
      </VStack>
    </Center>
  );
}
