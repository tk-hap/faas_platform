import React, { useState } from 'react';
import type { FunctionData } from '../App';
import { createFunction } from '../api';
import styles from './FunctionCreateForm.module.css';

const DEFAULT_FUNCTION_BODY = `def handler(ctx):
    """
    This function is the entry point for the function.
    It will be invoked by the FaaS platform.
    """
    return {
        "statusCode": 200,
        "message": "Hello World"
    }`;

const SUPPORTED_LANGUAGES = [
  { label: 'Python', value: 'python' },
  { label: 'Go', value: 'go' },
];

interface Props {
  onFunctionCreated: (fn: FunctionData) => void;
}

const FunctionCreateForm: React.FC<Props> = ({ onFunctionCreated }) => {
  const [language, setLanguage] = useState('python');
  const [body, setBody] = useState(DEFAULT_FUNCTION_BODY);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const fn = await createFunction(language, body);
      onFunctionCreated(fn);
    } catch (err: any) {
      setError(err.message || 'Error creating function');
    } finally {
      setLoading(false);
    }
  };

  return (
    <form className={styles.form} onSubmit={handleSubmit}>
      <label>
        Language:
        <select value={language} onChange={e => setLanguage(e.target.value)}>
          {SUPPORTED_LANGUAGES.map(lang => (
            <option key={lang.value} value={lang.value}>{lang.label}</option>
          ))}
        </select>
      </label>
      <label>
        Function Code:
        <textarea
          value={body}
          onChange={e => setBody(e.target.value)}
          rows={10}
          spellCheck={false}
        />
      </label>
      <button type="submit" disabled={loading}>{loading ? 'Creating...' : 'Create Function'}</button>
      {error && <div className={styles.error}>{error}</div>}
    </form>
  );
};

export default FunctionCreateForm; 