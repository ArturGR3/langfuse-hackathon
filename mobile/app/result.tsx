import { useState } from 'react';
import {
  View, Text, ScrollView, TouchableOpacity, StyleSheet
} from 'react-native';
import { useLocalSearchParams } from 'expo-router';
import { TranslationResult } from '../src/types';

export default function ResultScreen() {
  const { result } = useLocalSearchParams<{ result: string }>();
  const doc: TranslationResult = JSON.parse(result);
  const [translationExpanded, setTranslationExpanded] = useState(false);
  const [checked, setChecked] = useState<boolean[]>(doc.actions.map(() => false));

  return (
    <ScrollView style={styles.scroll} contentContainerStyle={styles.container}>
      <View style={styles.badge}>
        <Text style={styles.badgeText}>{doc.document_type.toUpperCase()}</Text>
      </View>

      <Text style={styles.label}>Summary</Text>
      <Text style={styles.body}>{doc.summary}</Text>

      <TouchableOpacity
        style={styles.row}
        onPress={() => setTranslationExpanded(v => !v)}
      >
        <Text style={styles.label}>Full Translation</Text>
        <Text style={styles.chevron}>{translationExpanded ? '▲' : '▼'}</Text>
      </TouchableOpacity>
      {translationExpanded && (
        <Text style={styles.translation}>{doc.translation}</Text>
      )}

      <Text style={styles.label}>Actions Required</Text>
      {doc.actions.map((action, i) => (
        <TouchableOpacity
          key={i}
          style={styles.actionRow}
          onPress={() => setChecked(prev => prev.map((v, j) => j === i ? !v : v))}
        >
          <Text style={styles.checkbox}>{checked[i] ? '☑' : '☐'}</Text>
          <View style={{ flex: 1 }}>
            <Text style={[styles.actionText, checked[i] && styles.done]}>
              {action.description}
            </Text>
            {action.deadline && (
              <Text style={styles.deadline}>Due: {action.deadline}</Text>
            )}
          </View>
        </TouchableOpacity>
      ))}

      <View style={styles.savedBanner}>
        <Text style={styles.savedText}>Saved to vault on your laptop</Text>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  scroll: { flex: 1, backgroundColor: '#F9FAFB' },
  container: { padding: 24, gap: 12 },
  badge: { backgroundColor: '#DBEAFE', paddingHorizontal: 12, paddingVertical: 4, borderRadius: 8, alignSelf: 'flex-start' },
  badgeText: { color: '#1D4ED8', fontWeight: '700', fontSize: 12 },
  label: { fontSize: 16, fontWeight: '700', color: '#111827', marginTop: 8 },
  body: { fontSize: 14, color: '#374151', lineHeight: 22 },
  row: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  chevron: { fontSize: 14, color: '#6B7280' },
  translation: { fontSize: 13, color: '#6B7280', lineHeight: 20, fontStyle: 'italic' },
  actionRow: { flexDirection: 'row', alignItems: 'flex-start', gap: 10, paddingVertical: 6 },
  checkbox: { fontSize: 20, color: '#3B82F6' },
  actionText: { fontSize: 14, color: '#374151' },
  done: { textDecorationLine: 'line-through', color: '#9CA3AF' },
  deadline: { fontSize: 12, color: '#EF4444', marginTop: 2 },
  savedBanner: { backgroundColor: '#D1FAE5', borderRadius: 8, padding: 12, marginTop: 16 },
  savedText: { color: '#065F46', fontWeight: '600' },
});
