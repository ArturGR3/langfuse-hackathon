export interface Action {
  description: string;
  deadline: string | null;
}

export interface TranslationResult {
  document_type: string;
  translation: string;
  summary: string;
  actions: Action[];
}
