import { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const COLORS = ['#2E75B6', '#1F4E79', '#4BACC6', '#70AD47', '#FF8C00'];

function App() {
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);
  const [aggregating, setAggregating] = useState(false);

  const fetchReports = async () => {
    try {
      const res = await axios.get(`${API_URL}/analytics/reports`);
      // Group by bucket and take the most recent report for each
      const byBucket = {};
      res.data.forEach(r => {
        if (!byBucket[r.bucket] || r.created_at > byBucket[r.bucket].created_at) {
          byBucket[r.bucket] = r;
        }
      });
      setReports(Object.values(byBucket));
      setLastUpdated(new Date().toLocaleTimeString());
      setError(null);
    } catch (err) {
      setError('Could not reach the analytics backend. Is it running?');
    } finally {
      setLoading(false);
    }
  };

  const triggerAggregation = async () => {
    setAggregating(true);
    try {
      await axios.post(`${API_URL}/analytics/aggregate/run`);
      await fetchReports();
    } catch (err) {
      setError('Aggregation failed: ' + err.message);
    } finally {
      setAggregating(false);
    }
  };

  useEffect(() => {
    fetchReports();
    const interval = setInterval(fetchReports, 30000); // refresh every 30s
    return () => clearInterval(interval);
  }, []);

  return (
    <div style={{ fontFamily: 'Arial, sans-serif', maxWidth: 960, margin: '0 auto', padding: '32px 16px' }}>
      <div style={{ marginBottom: 32 }}>
        <h1 style={{ color: '#1F4E79', marginBottom: 4 }}>Privacy-Preserving Analytics</h1>
        <p style={{ color: '#666', marginBottom: 16 }}>
          All values shown are population-level aggregates. No individual user data is stored or displayed.
        </p>
        <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
          <button
            onClick={triggerAggregation}
            disabled={aggregating}
            style={{ background: '#2E75B6', color: 'white', border: 'none',
                     padding: '10px 20px', borderRadius: 6, cursor: 'pointer', fontSize: 14 }}
          >
            {aggregating ? 'Running...' : 'Run Aggregation Now'}
          </button>
          <button
            onClick={fetchReports}
            style={{ background: '#eee', color: '#333', border: 'none',
                     padding: '10px 20px', borderRadius: 6, cursor: 'pointer', fontSize: 14 }}
          >
            Refresh
          </button>
          {lastUpdated && <span style={{ color: '#888', fontSize: 13 }}>Last updated: {lastUpdated}</span>}
        </div>
      </div>

      {loading && <p style={{ color: '#888' }}>Loading reports...</p>}
      {error && <p style={{ color: '#c0392b', background: '#fdecea', padding: 12, borderRadius: 6 }}>{error}</p>}

      {!loading && reports.length === 0 && !error && (
        <div style={{ background: '#f5f5f5', padding: 32, borderRadius: 8, textAlign: 'center' }}>
          <p style={{ color: '#888' }}>No reports yet. Send some events using the client SDK, then click 'Run Aggregation Now'.</p>
        </div>
      )}

      {reports.length > 0 && (
        <>
          <h2 style={{ color: '#1F4E79', marginTop: 32 }}>Aggregate Values by Event Type</h2>
          <ResponsiveContainer width='100%' height={320}>
            <BarChart data={reports} margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
              <CartesianGrid strokeDasharray='3 3' stroke='#eee' />
              <XAxis dataKey='bucket' tick={{ fontSize: 13 }} />
              <YAxis tick={{ fontSize: 13 }} />
              <Tooltip formatter={(v) => v.toFixed(2)} />
              <Bar dataKey='aggregate_value' radius={[4, 4, 0, 0]}>
                {reports.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>

          <h2 style={{ color: '#1F4E79', marginTop: 40 }}>Detail Table</h2>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 14 }}>
            <thead>
              <tr style={{ background: '#2E75B6', color: 'white' }}>
                <th style={{ padding: '12px 16px', textAlign: 'left' }}>Event Bucket</th>
                <th style={{ padding: '12px 16px', textAlign: 'right' }}>Aggregate Value</th>
                <th style={{ padding: '12px 16px', textAlign: 'right' }}>Events Included</th>
                <th style={{ padding: '12px 16px', textAlign: 'left' }}>Last Aggregated</th>
              </tr>
            </thead>
            <tbody>
              {reports.map((r, i) => (
                <tr key={r.bucket} style={{ background: i % 2 === 0 ? '#f9f9f9' : 'white' }}>
                  <td style={{ padding: '10px 16px', fontFamily: 'monospace' }}>{r.bucket}</td>
                  <td style={{ padding: '10px 16px', textAlign: 'right', fontWeight: 'bold' }}>
                    {r.aggregate_value.toFixed(2)}
                  </td>
                  <td style={{ padding: '10px 16px', textAlign: 'right' }}>{r.event_count}</td>
                  <td style={{ padding: '10px 16px', color: '#888' }}>{r.created_at}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}

      <div style={{ marginTop: 48, padding: '16px 20px', background: '#f0f7ff', borderRadius: 8, 
                    borderLeft: '4px solid #2E75B6', fontSize: 13, color: '#444' }}>
        <strong>How this works:</strong> Each user's browser encrypts their analytics data locally using Paillier
        homomorphic encryption before sending it. The server stores only ciphertexts. During aggregation,
        the server adds ciphertexts together without decrypting them, then decrypts only the final sum.
        Individual user data is never visible to the server or this dashboard.
      </div>
    </div>
  );
}

export default App;