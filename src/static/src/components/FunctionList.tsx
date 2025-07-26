import React, { useState, useEffect } from 'react';
import type { FunctionData } from '../App';
import styles from './FunctionList.module.css';

interface Props {
  latestFunction: FunctionData | null;
}

const FunctionList: React.FC<Props> = ({ latestFunction }) => {
  const [healthy, setHealthy] = useState<boolean | null>(null);
  const [loading, setLoading] = useState(false);

  const checkHealth = async () => {
    if (!latestFunction) return;
    setLoading(true);
    try {
      const res = await fetch(`/api/functions/${latestFunction.id}/health`);
      if (!res.ok) {
        setHealthy(false);
      } else {
        const data = await res.json();
        setHealthy(data === true);
      }
    } catch {
      setHealthy(false);
    } finally {
      setLoading(false);
    }
  };

  // Auto-check health when a new function appears
  useEffect(() => {
    if (latestFunction) {
      setHealthy(true); // Assume healthy initially since creation succeeded
      checkHealth(); // Then verify with actual health check
    }
  }, [latestFunction]);

  if (!latestFunction) return null;

  const getHealthDisplay = () => {
    if (loading) return <span style={{ color: 'orange' }}>Checking...</span>;
    if (healthy === null) return <span style={{ color: 'gray' }}>Unknown</span>;
    if (healthy) return <span style={{ color: 'green' }}>✓ Healthy</span>;
    return <span style={{ color: 'red' }}>✗ Unhealthy</span>;
  };

  return (
    <div className={styles.list}>
      <h2>Latest Created Function</h2>
      <div><strong>ID:</strong> {latestFunction.id}</div>
      <div><strong>Language:</strong> {latestFunction.language}</div>
      <div><strong>Created At:</strong> {new Date(latestFunction.created_at).toLocaleString()}</div>
      <div><strong>URL:</strong> <a href={latestFunction.url} target="_blank" rel="noopener noreferrer">{latestFunction.url}</a></div>
      <div>
        <strong>Status:</strong> {getHealthDisplay()}
        <button
          onClick={checkHealth}
          disabled={loading}
          style={{ marginLeft: '10px', padding: '4px 8px' }}
        >
          {loading ? 'Refreshing...' : 'Refresh'}
        </button>
      </div>
    </div>
  );
};

export default FunctionList; 