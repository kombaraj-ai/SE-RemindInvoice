'use client';
import { ChakraProvider, extendTheme } from '@chakra-ui/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider } from '@/context/AuthContext';

const theme = extendTheme({
  colors: {
    brand: {
      50: '#eef2ff',
      100: '#e0e7ff',
      200: '#c7d2fe',
      300: '#a5b4fc',
      400: '#818cf8',
      500: '#6366f1',
      600: '#4f46e5',
      700: '#4338ca',
      800: '#3730a3',
      900: '#312e81',
    },
  },
  fonts: {
    heading: 'Inter, sans-serif',
    body: 'Inter, sans-serif',
  },
  styles: {
    global: {
      body: { bg: '#f5f5fb', color: 'gray.800' },
    },
  },
  components: {
    Button: {
      baseStyle: { borderRadius: 'lg', fontWeight: '600' },
    },
    Input: {
      variants: {
        outline: {
          field: {
            borderRadius: 'lg',
            bg: 'white',
            _focus: { boxShadow: '0 0 0 3px rgba(99,102,241,0.18)', borderColor: 'brand.400' },
          },
        },
      },
    },
    Select: {
      variants: {
        outline: {
          field: { borderRadius: 'lg', bg: 'white' },
        },
      },
    },
  },
});

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { staleTime: 1000 * 60, retry: 1 },
  },
});

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap"
          rel="stylesheet"
        />
        <title>RemindInvoice — Get Paid Faster</title>
      </head>
      <body>
        <QueryClientProvider client={queryClient}>
          <ChakraProvider theme={theme}>
            <AuthProvider>{children}</AuthProvider>
          </ChakraProvider>
        </QueryClientProvider>
      </body>
    </html>
  );
}
