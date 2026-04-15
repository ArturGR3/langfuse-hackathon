import { useState } from 'react';
import {
  View, Text, TouchableOpacity, ActivityIndicator,
  StyleSheet, Alert
} from 'react-native';
import * as ImagePicker from 'expo-image-picker';
import { useRouter } from 'expo-router';
import { TranslationResult } from '../src/types';

const API_BASE = process.env.EXPO_PUBLIC_API_BASE_URL;

export default function HomeScreen() {
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  async function pickAndProcess() {
    const permission = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (!permission.granted) {
      Alert.alert('Permission required', 'Please allow photo library access.');
      return;
    }

    const picked = await ImagePicker.launchImageLibraryAsync({ quality: 0.8 });
    if (picked.canceled) return;

    setLoading(true);
    try {
      const formData = new FormData();
      formData.append('file', {
        uri: picked.assets[0].uri,
        name: 'document.jpg',
        type: 'image/jpeg',
      } as any);

      const response = await fetch(`${API_BASE}/process`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) throw new Error(`Server error: ${response.status}`);

      const result: TranslationResult = await response.json();
      router.push({ pathname: '/result', params: { result: JSON.stringify(result) } });
    } catch (err: any) {
      Alert.alert('Error', err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <View style={styles.container}>
      <Text style={styles.title}>German Paperwork Assistant</Text>
      <Text style={styles.subtitle}>Upload a German document to translate and get action items</Text>
      {loading ? (
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#3B82F6" />
          <Text style={styles.status}>Processing document...</Text>
        </View>
      ) : (
        <TouchableOpacity style={styles.button} onPress={pickAndProcess}>
          <Text style={styles.buttonText}>Upload Document</Text>
        </TouchableOpacity>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, alignItems: 'center', justifyContent: 'center', padding: 24, backgroundColor: '#F9FAFB' },
  title: { fontSize: 24, fontWeight: 'bold', marginBottom: 8, textAlign: 'center' },
  subtitle: { fontSize: 14, color: '#6B7280', textAlign: 'center', marginBottom: 40 },
  button: { backgroundColor: '#3B82F6', paddingHorizontal: 32, paddingVertical: 16, borderRadius: 12 },
  buttonText: { color: '#fff', fontSize: 16, fontWeight: '600' },
  loadingContainer: { alignItems: 'center', gap: 16 },
  status: { fontSize: 14, color: '#6B7280' },
});
