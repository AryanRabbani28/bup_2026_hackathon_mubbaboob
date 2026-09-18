import { useState } from 'react';
import axios from 'axios';

function App() {
  const [scenario, setScenario] = useState('');
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState('');

  const handleOptimize = async () => {
    try {
      setError('');
      setResult(null);
      const payload = JSON.parse(scenario);
      const url = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
      const response = await axios.post(`${url}/optimize-energy`, payload);
      setResult(response.data);
    } catch (err: any) {
      if (err.response) {
        setError(JSON.stringify(err.response.data, null, 2));
      } else {
        setError(err.message);
      }
    }
  };

  return (
    <div style={{ padding: '20px', fontFamily: 'sans-serif' }}>
      <h1>GridWise Smart Campus Energy Optimization</h1>
      
      <div style={{ display: 'flex', gap: '20px' }}>
        <div style={{ flex: 1 }}>
          <h3>Input Scenario (JSON)</h3>
          <textarea 
            style={{ width: '100%', height: '400px', fontFamily: 'monospace' }}
            value={scenario}
            onChange={(e) => setScenario(e.target.value)}
            placeholder='Paste JSON scenario here'
          />
          <br/>
          <button onClick={handleOptimize} style={{ marginTop: '10px', padding: '10px', cursor: 'pointer' }}>
            Submit / Optimize
          </button>
          
          {error && (
            <div style={{ marginTop: '20px', color: 'red' }}>
              <h4>Error</h4>
              <pre>{error}</pre>
            </div>
          )}
        </div>
        
        <div style={{ flex: 1 }}>
          <h3>Results</h3>
          {result ? (
            <div>
              <p><strong>Scenario ID:</strong> {result.scenario_id}</p>
              <p><strong>Total Cost (BDT):</strong> {result.total_cost_bdt}</p>
              <p><strong>Total Grid (kWh):</strong> {result.total_grid_kwh}</p>
              <p><strong>Peak Grid (kWh):</strong> {result.peak_grid_kwh}</p>
              <p><strong>Plan Summary:</strong> {result.plan_summary}</p>
              
              <h4>Directive Interpretation</h4>
              <pre style={{ background: '#eee', padding: '10px' }}>
                {JSON.stringify(result.directive_interpretation, null, 2)}
              </pre>

              <h4>Hourly Plan</h4>
              <table border={1} cellPadding={5} style={{ borderCollapse: 'collapse', width: '100%', textAlign: 'center' }}>
                <thead>
                  <tr>
                    <th>Hour</th>
                    <th>Grid kWh</th>
                    <th>Solar kWh</th>
                    <th>Battery Action</th>
                    <th>Battery kWh</th>
                    <th>Energy After</th>
                  </tr>
                </thead>
                <tbody>
                  {result.hourly_plan.map((h: any) => (
                    <tr key={h.hour}>
                      <td>{h.hour}</td>
                      <td>{h.grid_kwh.toFixed(2)}</td>
                      <td>{h.solar_used_kwh.toFixed(2)}</td>
                      <td>{h.battery_action}</td>
                      <td>{h.battery_kwh.toFixed(2)}</td>
                      <td>{h.battery_energy_after_kwh.toFixed(2)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p>No results yet.</p>
          )}
        </div>
      </div>
    </div>
  );
}

export default App;
