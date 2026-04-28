'use client';
import {
  Box,
  Button,
  HStack,
  Heading,
  Text,
  Badge,
  VStack,
  Divider,
  Spinner,
  Center,
  SimpleGrid,
  Avatar,
  Link,
  Progress,
  Flex,
  Icon,
  useToast,
} from '@chakra-ui/react';
import { useQuery } from '@tanstack/react-query';
import { useRouter, useSearchParams } from 'next/navigation';
import { useEffect, useState } from 'react';
import { Settings, User, Bell, CreditCard, ExternalLink, ChevronRight, Check, Zap, Star } from 'lucide-react';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { AppShell } from '@/components/layout/AppShell';
import { GlassCard } from '@/components/ui/GlassCard';
import { GradientButton } from '@/components/ui/GradientButton';
import { PageWrapper } from '@/components/layout/PageWrapper';
import { remindersService } from '@/services/reminders';
import { subscriptionService } from '@/services/subscription';
import { useAuth } from '@/context/AuthContext';
import type { TriggerType } from '@/types/reminder';

const TRIGGER_LABELS: Record<TriggerType, string> = {
  before_due: 'Before Due',
  on_due: 'On Due Date',
  after_due: 'After Due',
};

const PLAN_LIMITS: Record<string, number> = { free: 5, silver: 50, gold: 100 };
const PLAN_COLORS: Record<string, string> = { free: 'gray', silver: 'blue', gold: 'yellow' };

interface PricingCardProps {
  name: string;
  price: number;
  invoices: number;
  features: string[];
  isCurrent: boolean;
  isPopular?: boolean;
  gradient: string;
  accentColor: string;
  onUpgrade: () => void;
  isLoading: boolean;
}

function PricingCard({
  name, price, invoices, features, isCurrent, isPopular,
  gradient, accentColor, onUpgrade, isLoading,
}: PricingCardProps) {
  return (
    <Box
      borderRadius="2xl"
      overflow="hidden"
      border="2px solid"
      borderColor={isCurrent ? accentColor : 'gray.100'}
      boxShadow={isCurrent ? `0 0 0 3px ${accentColor}30` : '0 2px 16px rgba(0,0,0,0.06)'}
      transition="all 0.2s"
      _hover={{ transform: 'translateY(-2px)', boxShadow: `0 8px 28px rgba(0,0,0,0.1)` }}
      position="relative"
    >
      {isPopular && (
        <Box
          position="absolute"
          top={3}
          right={3}
          bg="orange.400"
          color="white"
          fontSize="10px"
          fontWeight="700"
          px={2}
          py={0.5}
          borderRadius="full"
          textTransform="uppercase"
          letterSpacing="wider"
        >
          Popular
        </Box>
      )}
      <Box bgGradient={gradient} px={5} py={4}>
        <Text fontWeight="800" fontSize="lg" color="white">{name}</Text>
        <HStack align="baseline" spacing={1} mt={1}>
          <Text fontSize="2xl" fontWeight="900" color="white">
            {price === 0 ? 'Free' : `₹${price}`}
          </Text>
          {price > 0 && <Text fontSize="sm" color="whiteAlpha.800">/month</Text>}
        </HStack>
      </Box>
      <Box bg="white" px={5} py={4}>
        <Text fontSize="sm" color="gray.500" mb={3}>
          Up to <Text as="span" fontWeight="700" color="gray.800">{invoices} invoices</Text>/month
        </Text>
        <VStack align="stretch" spacing={2} mb={4}>
          {features.map((f) => (
            <HStack key={f} spacing={2}>
              <Box color="green.500" flexShrink={0}><Check size={14} /></Box>
              <Text fontSize="sm" color="gray.600">{f}</Text>
            </HStack>
          ))}
        </VStack>
        {isCurrent ? (
          <Button w="full" variant="outline" borderColor={accentColor} color={accentColor} isDisabled borderRadius="xl" size="sm">
            Current Plan
          </Button>
        ) : (
          <GradientButton w="full" size="sm" onClick={onUpgrade} isLoading={isLoading} loadingText="Redirecting...">
            Upgrade Now
          </GradientButton>
        )}
      </Box>
    </Box>
  );
}

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString('en-IN', {
    year: 'numeric', month: 'long', day: 'numeric',
  });
}

function SettingsContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { user, refreshUser } = useAuth();
  const toast = useToast();
  const [upgradingPlan, setUpgradingPlan] = useState<string | null>(null);

  const { data: rules, isLoading: rulesLoading } = useQuery({
    queryKey: ['reminder-rules'],
    queryFn: () => remindersService.listRules(),
  });

  const { data: planStatus, refetch: refetchPlan } = useQuery({
    queryKey: ['plan-status'],
    queryFn: () => subscriptionService.getStatus(),
    enabled: !!user,
  });

  useEffect(() => {
    const payment = searchParams.get('payment');
    const plan = searchParams.get('plan');
    if (payment === 'success' && plan) {
      toast({
        title: '🎉 Payment successful!',
        description: `Your account has been upgraded to the ${plan.charAt(0).toUpperCase() + plan.slice(1)} plan.`,
        status: 'success',
        duration: 6000,
        isClosable: true,
      });
      refreshUser();
      refetchPlan();
    } else if (payment === 'cancelled') {
      toast({ title: 'Payment cancelled', status: 'info', duration: 3000 });
    }
  }, [searchParams]);  // eslint-disable-line react-hooks/exhaustive-deps

  const handleUpgrade = async (plan: 'silver' | 'gold') => {
    setUpgradingPlan(plan);
    try {
      const { payment_url } = await subscriptionService.createCheckout(plan);
      window.location.href = payment_url;
    } catch {
      toast({
        title: 'Could not start checkout',
        description: 'Payment processing is not configured yet. Please contact support.',
        status: 'error',
        duration: 4000,
        isClosable: true,
      });
      setUpgradingPlan(null);
    }
  };

  if (!user) {
    return <Center py={20}><Spinner size="xl" color="brand.500" /></Center>;
  }

  const activeRules = rules?.filter((r) => r.is_active) ?? [];
  const currentPlan = user.plan || 'free';
  const limit = planStatus?.monthly_invoice_limit ?? PLAN_LIMITS[currentPlan] ?? 5;
  const used = planStatus?.monthly_invoice_count ?? user.monthly_invoice_count ?? 0;
  const usagePct = Math.min(100, (used / limit) * 100);

  return (
    <PageWrapper>
      <HStack spacing={3} mb={8}>
        <Settings size={22} color="#6366f1" />
        <Heading size="lg" bgGradient="linear(to-r, brand.600, purple.500)" bgClip="text" fontWeight="800">
          Settings
        </Heading>
      </HStack>

      <SimpleGrid columns={{ base: 1, lg: 2 }} spacing={6}>
        {/* Left column */}
        <VStack spacing={6} align="stretch">
          {/* Account */}
          <GlassCard>
            <HStack justify="space-between" mb={4}>
              <HStack spacing={2}>
                <User size={17} color="#6366f1" />
                <Heading size="sm" color="gray.700">Account</Heading>
              </HStack>
              <GradientButton size="sm" rightIcon={<ExternalLink size={13} />} onClick={() => router.push('/profile')}>
                Edit Profile
              </GradientButton>
            </HStack>
            <HStack spacing={4} mb={4}>
              <Avatar name={user.full_name ?? user.email} src={user.avatar_url ?? undefined} size="lg" bg="brand.500" color="white" />
              <VStack align="flex-start" spacing={1}>
                <Text fontWeight="700" color="gray.800" fontSize="lg">{user.full_name ?? 'No name set'}</Text>
                <Text fontSize="sm" color="gray.500">{user.email}</Text>
                <HStack spacing={1}>
                  <Badge colorScheme={PLAN_COLORS[currentPlan]} borderRadius="full" px={2} fontSize="xs" textTransform="capitalize">
                    {currentPlan} Plan
                  </Badge>
                  {user.oauth_provider && (
                    <Badge colorScheme="blue" borderRadius="full" px={2} fontSize="xs">{user.oauth_provider} OAuth</Badge>
                  )}
                </HStack>
              </VStack>
            </HStack>
            <Divider mb={4} />
            <VStack align="stretch" spacing={3}>
              <HStack justify="space-between">
                <Text fontSize="sm" color="gray.500">Member Since</Text>
                <Text fontSize="sm" fontWeight="600" color="gray.800">{formatDate(user.created_at)}</Text>
              </HStack>
              <Divider />
              <HStack justify="space-between">
                <Text fontSize="sm" color="gray.500">Account Status</Text>
                <Badge colorScheme={user.is_active ? 'green' : 'gray'} borderRadius="full" px={2} fontSize="xs">
                  {user.is_active ? 'Active' : 'Inactive'}
                </Badge>
              </HStack>
              {user.is_admin && (
                <>
                  <Divider />
                  <HStack justify="space-between">
                    <Text fontSize="sm" color="gray.500">Role</Text>
                    <Badge colorScheme="purple" borderRadius="full" px={2} fontSize="xs">Admin</Badge>
                  </HStack>
                </>
              )}
            </VStack>
          </GlassCard>

          {/* Usage */}
          <GlassCard>
            <HStack spacing={2} mb={4}>
              <Zap size={17} color="#6366f1" />
              <Heading size="sm" color="gray.700">Monthly Usage</Heading>
            </HStack>
            <Flex justify="space-between" align="center" mb={2}>
              <Text fontSize="sm" color="gray.600">Invoices this month</Text>
              <Text fontSize="sm" fontWeight="700" color={usagePct >= 100 ? 'red.500' : 'gray.800'}>
                {used} / {limit}
              </Text>
            </Flex>
            <Progress
              value={usagePct}
              colorScheme={usagePct >= 100 ? 'red' : usagePct >= 80 ? 'orange' : 'brand'}
              borderRadius="full"
              size="sm"
              mb={2}
              hasStripe={usagePct < 100}
            />
            {usagePct >= 100 ? (
              <Text fontSize="xs" color="red.500" fontWeight="600">
                ⚠ Limit reached — upgrade to create more invoices
              </Text>
            ) : (
              <Text fontSize="xs" color="gray.400">
                {planStatus?.invoices_remaining ?? limit - used} invoices remaining
              </Text>
            )}
            {user.plan_expires_at && (
              <Text fontSize="xs" color="gray.400" mt={2}>
                Plan expires: {formatDate(user.plan_expires_at)}
              </Text>
            )}
          </GlassCard>

          {/* Reminder Rules */}
          <GlassCard>
            <HStack justify="space-between" mb={4}>
              <HStack spacing={2}>
                <Bell size={17} color="#6366f1" />
                <Heading size="sm" color="gray.700">Reminder Rules</Heading>
              </HStack>
              <Button size="sm" variant="ghost" colorScheme="brand" rightIcon={<ChevronRight size={14} />} onClick={() => router.push('/reminders')}>
                Manage
              </Button>
            </HStack>
            {rulesLoading ? (
              <Center py={6}><Spinner size="sm" color="brand.500" /></Center>
            ) : !rules || rules.length === 0 ? (
              <Box p={4} bg="gray.50" borderRadius="lg" border="1px dashed" borderColor="gray.200" textAlign="center">
                <Text fontSize="sm" color="gray.400" mb={2}>No reminder rules configured</Text>
                <Button size="xs" colorScheme="brand" variant="outline" onClick={() => router.push('/reminders')}>Create your first rule</Button>
              </Box>
            ) : (
              <VStack align="stretch" spacing={3}>
                <Text fontSize="xs" color="gray.400" textTransform="uppercase" letterSpacing="wide">
                  {rules.length} rule{rules.length !== 1 ? 's' : ''} • {activeRules.length} active
                </Text>
                <Divider />
                {rules.slice(0, 4).map((rule) => (
                  <HStack key={rule.id} justify="space-between">
                    <VStack align="flex-start" spacing={0}>
                      <Text fontSize="sm" fontWeight="600" color="gray.800">{rule.name}</Text>
                      <Text fontSize="xs" color="gray.400">
                        {TRIGGER_LABELS[rule.trigger_type]}{rule.days_offset > 0 ? ` — ${rule.days_offset}d` : ''}
                      </Text>
                    </VStack>
                    <Badge colorScheme={rule.is_active ? 'green' : 'gray'} borderRadius="full" px={2} fontSize="xs">
                      {rule.is_active ? 'Active' : 'Off'}
                    </Badge>
                  </HStack>
                ))}
                {rules.length > 4 && (
                  <Link fontSize="xs" color="brand.500" onClick={() => router.push('/reminders')} cursor="pointer">
                    View all {rules.length} rules →
                  </Link>
                )}
              </VStack>
            )}
          </GlassCard>
        </VStack>

        {/* Right column — Pricing */}
        <VStack spacing={6} align="stretch">
          <GlassCard>
            <HStack spacing={2} mb={5}>
              <Star size={17} color="#6366f1" />
              <Heading size="sm" color="gray.700">Upgrade Plan</Heading>
            </HStack>

            <VStack spacing={4} align="stretch">
              <PricingCard
                name="Free"
                price={0}
                invoices={5}
                features={['5 invoices/month', 'Client management', 'PDF export', 'Email reminders']}
                isCurrent={currentPlan === 'free'}
                gradient="linear(to-r, gray.500, gray.600)"
                accentColor="#718096"
                onUpgrade={() => {}}
                isLoading={false}
              />
              <PricingCard
                name="Silver"
                price={5}
                invoices={50}
                features={['50 invoices/month', 'Everything in Free', 'Priority email support', 'Advanced reminders']}
                isCurrent={currentPlan === 'silver'}
                isPopular
                gradient="linear(to-r, blue.400, brand.500)"
                accentColor="#6366f1"
                onUpgrade={() => handleUpgrade('silver')}
                isLoading={upgradingPlan === 'silver'}
              />
              <PricingCard
                name="Gold"
                price={10}
                invoices={100}
                features={['100 invoices/month', 'Everything in Silver', 'Custom branding', 'Analytics dashboard']}
                isCurrent={currentPlan === 'gold'}
                gradient="linear(to-r, orange.400, yellow.500)"
                accentColor="#ED8936"
                onUpgrade={() => handleUpgrade('gold')}
                isLoading={upgradingPlan === 'gold'}
              />
            </VStack>
          </GlassCard>

          {/* Quick Links */}
          <GlassCard>
            <Heading size="sm" color="gray.700" mb={4}>Quick Links</Heading>
            <VStack align="stretch" spacing={2}>
              {[
                { label: 'My Profile', path: '/profile', icon: User },
                { label: 'Reminder Rules', path: '/reminders', icon: Bell },
                { label: 'Clients', path: '/clients', icon: User },
              ].map(({ label, path, icon: Icon }) => (
                <HStack key={path} justify="space-between" p={3} borderRadius="lg" border="1px solid" borderColor="gray.100"
                  cursor="pointer" _hover={{ bg: 'brand.50', borderColor: 'brand.200' }} transition="all 0.15s" onClick={() => router.push(path)}>
                  <HStack spacing={3}>
                    <Box color="brand.500"><Icon size={15} /></Box>
                    <Text fontSize="sm" fontWeight="500" color="gray.700">{label}</Text>
                  </HStack>
                  <ChevronRight size={14} color="#9CA3AF" />
                </HStack>
              ))}
              {user.is_admin && (
                <HStack justify="space-between" p={3} borderRadius="lg" border="1px solid" borderColor="purple.100"
                  cursor="pointer" _hover={{ bg: 'purple.50', borderColor: 'purple.200' }} transition="all 0.15s" onClick={() => router.push('/admin')}>
                  <HStack spacing={3}>
                    <Box color="purple.500"><Settings size={15} /></Box>
                    <Text fontSize="sm" fontWeight="500" color="purple.700">Admin Panel</Text>
                  </HStack>
                  <ChevronRight size={14} color="#9CA3AF" />
                </HStack>
              )}
            </VStack>
          </GlassCard>
        </VStack>
      </SimpleGrid>
    </PageWrapper>
  );
}

export default function SettingsPage() {
  return (
    <ProtectedRoute>
      <AppShell>
        <SettingsContent />
      </AppShell>
    </ProtectedRoute>
  );
}
