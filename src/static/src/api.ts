import type { FunctionData } from './App';

export async function createFunction(language: string, body: string): Promise<FunctionData> {
  const res = await fetch('/api/functions', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ language, body }),
  });
  if (!res.ok) {
    throw new Error('Failed to create function');
  }
  return res.json();
} 