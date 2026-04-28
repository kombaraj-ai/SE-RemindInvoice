'use client';
import {
  Box,
  Flex,
  Text,
  VStack,
  Avatar,
  IconButton,
  Tooltip,
  Divider,
  HStack,
  Badge,
} from '@chakra-ui/react';
import { usePathname, useRouter } from 'next/navigation';
import {
  Home,
  FileText,
  Users,
  Bell,
  Settings,
  Shield,
  LogOut,
} from 'lucide-react';
import { useAuth } from '@/context/AuthContext';

interface NavItem {
  label: string;
  href: string;
  icon: React.ReactNode;
  adminOnly?: boolean;
  badge?: string;
}

const navItems: NavItem[] = [
  { label: 'Dashboard', href: '/dashboard', icon: <Home size={18} /> },
  { label: 'Invoices', href: '/invoices', icon: <FileText size={18} /> },
  { label: 'Clients', href: '/clients', icon: <Users size={18} /> },
  { label: 'Reminders', href: '/reminders', icon: <Bell size={18} /> },
  { label: 'Settings', href: '/settings', icon: <Settings size={18} /> },
  { label: 'Admin', href: '/admin', icon: <Shield size={18} />, adminOnly: true },
];

export function Sidebar() {
  const { user, logout } = useAuth();
  const pathname = usePathname();
  const router = useRouter();

  const handleLogout = () => {
    logout();
    router.push('/login');
  };

  const visibleItems = navItems.filter(
    (item) => !item.adminOnly || (item.adminOnly && user?.is_admin)
  );

  return (
    <Box
      w="240px"
      minH="100vh"
      bgGradient="linear(to-b, #1e1b4b, #2e2a72)"
      display="flex"
      flexDirection="column"
      py={6}
      px={3}
      position="sticky"
      top={0}
      h="100vh"
      overflowY="auto"
    >
      {/* Logo */}
      <Box mb={8} px={3}>
        <Text
          fontSize="xl"
          fontWeight="800"
          bgGradient="linear(to-r, #a5b4fc, #c4b5fd)"
          bgClip="text"
          letterSpacing="-0.5px"
        >
          RemindInvoice
        </Text>
        <Text fontSize="xs" color="whiteAlpha.500" mt={0.5} fontWeight="400">
          Invoice & Payment SaaS
        </Text>
      </Box>

      {/* Navigation */}
      <VStack spacing={1} align="stretch" flex={1}>
        {visibleItems.map((item) => {
          const isActive = pathname === item.href || pathname.startsWith(item.href + '/');
          return (
            <Tooltip key={item.href} label={item.label} placement="right" hasArrow openDelay={500}>
              <Flex
                as="button"
                onClick={() => router.push(item.href)}
                align="center"
                gap={3}
                px={3}
                py={2.5}
                borderRadius="xl"
                fontWeight={isActive ? '600' : '400'}
                color={isActive ? 'white' : 'whiteAlpha.600'}
                bg={isActive ? 'whiteAlpha.200' : 'transparent'}
                borderLeft={isActive ? '3px solid' : '3px solid transparent'}
                borderColor={isActive ? '#818cf8' : 'transparent'}
                _hover={{
                  bg: 'whiteAlpha.100',
                  color: 'white',
                }}
                transition="all 0.15s"
                w="full"
                textAlign="left"
              >
                <Box color={isActive ? '#a5b4fc' : 'whiteAlpha.500'}>
                  {item.icon}
                </Box>
                <Text fontSize="sm">{item.label}</Text>
                {item.badge && (
                  <Badge ml="auto" colorScheme="purple" fontSize="10px" borderRadius="full">
                    {item.badge}
                  </Badge>
                )}
              </Flex>
            </Tooltip>
          );
        })}
      </VStack>

      {/* User section */}
      <Box>
        <Divider borderColor="whiteAlpha.200" mb={4} />
        <HStack spacing={3} px={2}>
          <Avatar
            size="sm"
            name={user?.full_name ?? user?.email ?? 'User'}
            src={user?.avatar_url ?? undefined}
            bg="brand.500"
            border="2px solid"
            borderColor="whiteAlpha.300"
          />
          <Box flex={1} overflow="hidden">
            <Text fontSize="sm" fontWeight="600" noOfLines={1} color="white">
              {user?.full_name ?? 'User'}
            </Text>
            <Text fontSize="xs" color="whiteAlpha.500" noOfLines={1}>
              {user?.email}
            </Text>
          </Box>
          <Tooltip label="Logout" placement="top">
            <IconButton
              aria-label="Logout"
              icon={<LogOut size={15} />}
              size="sm"
              variant="ghost"
              color="whiteAlpha.600"
              _hover={{ color: 'red.300', bg: 'whiteAlpha.100' }}
              onClick={handleLogout}
            />
          </Tooltip>
        </HStack>
      </Box>
    </Box>
  );
}
