import { Stack } from 'expo-router';

export default function RootLayout() {
  return (
    <Stack>
      <Stack.Screen name="index" options={{ title: 'Paperwork Assistant' }} />
      <Stack.Screen name="result" options={{ title: 'Document Result' }} />
    </Stack>
  );
}
