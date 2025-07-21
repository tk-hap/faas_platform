import React from 'react';
import type { FunctionData } from '../App';
import styles from './FunctionList.module.css';

interface Props {
  latestFunction: FunctionData | null;
}

const FunctionList: React.FC<Props> = ({ latestFunction }) => {
  if (!latestFunction) return null;
  return (
    <div className={styles.list}>
      <h2>Latest Created Function</h2>
      <div><strong>ID:</strong> {latestFunction.id}</div>
      <div><strong>Language:</strong> {latestFunction.language}</div>
      <div><strong>Created At:</strong> {new Date(latestFunction.created_at).toLocaleString()}</div>
      <div><strong>URL:</strong> <a href={latestFunction.url} target="_blank" rel="noopener noreferrer">{latestFunction.url}</a></div>
    </div>
  );
};

export default FunctionList; 