import React, { useState } from 'react';
import type { FunctionData } from '../App';
import { createFunction } from '../api';
import styles from './FunctionCreateForm.module.css';

const DEFAULT_PY_FUNCTION_BODY = `from runtime_models import Event, Context, Response

def handler(event: Event, ctx: Context):
    # User logic: can return dict (JSON), (dict, status), or Response()
    return {
        "message": "Hello World",
        "function_id": ctx.function_id,
        "request_id": ctx.request_id,
        "path": event.path,
        "contract": ctx.contract_version,
    }`;

const DEFAULT_GO_FUNCTION_BODY = `package main

// Handle is the user function entrypoint.
func Handle(event Event, ctx Context) (Result, error) {
	return Result{
		StatusCode: 200,
		Body: map[string]string{
			"message":     "Hello World",
			"function_id": ctx.FunctionID,
			"request_id":  ctx.RequestID,
			"path":        event.Path,
			"contract":    ctx.ContractVersion,
		},
	}, nil
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
  const [body, setBody] = useState(DEFAULT_PY_FUNCTION_BODY);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleLanguageChange = (val: string) => {
    setLanguage(val);
    // Replace editor content with the corresponding default template
    if (val === 'python') {
      setBody(DEFAULT_PY_FUNCTION_BODY);
    } else if (val === 'go') {
      setBody(DEFAULT_GO_FUNCTION_BODY);
    }
  };

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
        <select value={language} onChange={e => handleLanguageChange(e.target.value)}>
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
          rows={14}
          spellCheck={false}
        />
      </label>
      <button type="submit" disabled={loading}>{loading ? 'Creating...' : 'Create Function'}</button>
      {error && <div className={styles.error}>{error}</div>}
    </form>
  );
};

export default FunctionCreateForm;