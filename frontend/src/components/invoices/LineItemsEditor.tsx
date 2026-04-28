'use client';
import {
  Box,
  Button,
  HStack,
  Input,
  Text,
  VStack,
  IconButton,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  TableContainer,
  Divider,
} from '@chakra-ui/react';
import { Plus, Trash2 } from 'lucide-react';

interface LineItem {
  description: string;
  quantity: number;
  unit_price: number;
  sort_order: number;
}

interface Props {
  items: LineItem[];
  onChange: (items: LineItem[]) => void;
}

export function LineItemsEditor({ items, onChange }: Props) {
  const addRow = () => {
    const newItem: LineItem = {
      description: '',
      quantity: 1,
      unit_price: 0,
      sort_order: items.length,
    };
    onChange([...items, newItem]);
  };

  const removeRow = (index: number) => {
    const updated = items
      .filter((_, i) => i !== index)
      .map((item, i) => ({ ...item, sort_order: i }));
    onChange(updated);
  };

  const updateRow = (index: number, field: keyof LineItem, value: string | number) => {
    const updated = items.map((item, i) => {
      if (i !== index) return item;
      return { ...item, [field]: value };
    });
    onChange(updated);
  };

  const getAmount = (item: LineItem): number => {
    return item.quantity * item.unit_price;
  };

  const subtotal = items.reduce((sum, item) => sum + getAmount(item), 0);

  return (
    <VStack spacing={0} align="stretch">
      <TableContainer>
        <Table size="sm" variant="simple">
          <Thead bg="gray.50">
            <Tr>
              <Th w="40%" color="gray.500" fontSize="xs" textTransform="uppercase" letterSpacing="wider">
                Description
              </Th>
              <Th w="15%" color="gray.500" fontSize="xs" textTransform="uppercase" letterSpacing="wider" isNumeric>
                Qty
              </Th>
              <Th w="20%" color="gray.500" fontSize="xs" textTransform="uppercase" letterSpacing="wider" isNumeric>
                Unit Price
              </Th>
              <Th w="20%" color="gray.500" fontSize="xs" textTransform="uppercase" letterSpacing="wider" isNumeric>
                Amount
              </Th>
              <Th w="5%" />
            </Tr>
          </Thead>
          <Tbody>
            {items.map((item, index) => (
              <Tr key={index}>
                <Td>
                  <Input
                    size="sm"
                    value={item.description}
                    onChange={(e) => updateRow(index, 'description', e.target.value)}
                    placeholder="Item description"
                    variant="filled"
                    bg="gray.50"
                    _hover={{ bg: 'gray.100' }}
                    _focus={{ bg: 'white', borderColor: 'brand.500' }}
                  />
                </Td>
                <Td isNumeric>
                  <Input
                    size="sm"
                    type="number"
                    min={0}
                    value={item.quantity}
                    onChange={(e) => updateRow(index, 'quantity', parseFloat(e.target.value) || 0)}
                    textAlign="right"
                    variant="filled"
                    bg="gray.50"
                    _hover={{ bg: 'gray.100' }}
                    _focus={{ bg: 'white', borderColor: 'brand.500' }}
                  />
                </Td>
                <Td isNumeric>
                  <Input
                    size="sm"
                    type="number"
                    min={0}
                    step="0.01"
                    value={item.unit_price}
                    onChange={(e) => updateRow(index, 'unit_price', parseFloat(e.target.value) || 0)}
                    textAlign="right"
                    variant="filled"
                    bg="gray.50"
                    _hover={{ bg: 'gray.100' }}
                    _focus={{ bg: 'white', borderColor: 'brand.500' }}
                  />
                </Td>
                <Td isNumeric>
                  <Text fontSize="sm" fontWeight="500" color="gray.700">
                    ₹{getAmount(item).toFixed(2)}
                  </Text>
                </Td>
                <Td>
                  <IconButton
                    aria-label="Remove item"
                    icon={<Trash2 size={14} />}
                    size="xs"
                    variant="ghost"
                    colorScheme="red"
                    onClick={() => removeRow(index)}
                    isDisabled={items.length === 1}
                  />
                </Td>
              </Tr>
            ))}
            {items.length === 0 && (
              <Tr>
                <Td colSpan={5}>
                  <Text color="gray.400" fontSize="sm" textAlign="center" py={4}>
                    No items yet. Click Add Item to get started.
                  </Text>
                </Td>
              </Tr>
            )}
          </Tbody>
        </Table>
      </TableContainer>

      <Divider />

      <HStack justify="space-between" px={4} py={3} bg="gray.50">
        <Button
          leftIcon={<Plus size={14} />}
          size="sm"
          variant="ghost"
          colorScheme="brand"
          onClick={addRow}
          color="brand.500"
          _hover={{ bg: 'brand.50' }}
        >
          Add Item
        </Button>
        <HStack spacing={4}>
          <Text fontSize="sm" color="gray.500">
            Subtotal:
          </Text>
          <Text fontSize="sm" fontWeight="700" color="gray.800">
            ₹{subtotal.toFixed(2)}
          </Text>
        </HStack>
      </HStack>
    </VStack>
  );
}
