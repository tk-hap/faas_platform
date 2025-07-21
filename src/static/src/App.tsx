import React, { useState } from 'react';
import FunctionCreateForm from './components/FunctionCreateForm';
import FunctionList from './components/FunctionList';
import styles from './App.module.css';

export interface FunctionData {
  id: string;
  language: string;
  created_at: string;
  url: string;
}

const App: React.FC = () => {
  const [latestFunction, setLatestFunction] = useState<FunctionData | null>(null);

  return (
    <div className={styles.container}>
      <h1>Function as a Service Platform</h1>
      <p>Create and deploy serverless functions in multiple languages</p>
      <FunctionCreateForm onFunctionCreated={setLatestFunction} />
      <FunctionList latestFunction={latestFunction} />
    </div>
  );
};

export default App; 