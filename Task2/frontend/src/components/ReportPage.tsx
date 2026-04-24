import React, { useState, useEffect } from 'react';
import { useKeycloak } from '@react-keycloak/web';

const ReportPage: React.FC = () => {
  const { keycloak, initialized } = useKeycloak();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [pkceInfo, setPkceInfo] = useState<string | null>(null);

  useEffect(() => {
    if (keycloak && initialized) {
      const checkPKCE = () => {
        const urlParams = new URLSearchParams(window.location.search);
        const codeChallenge = urlParams.get('code_challenge');
        const codeChallengeMethod = urlParams.get('code_challenge_method');

        if (codeChallenge && codeChallengeMethod === 'S256') {
          setPkceInfo(`PKCE активен! code_challenge найден в URL (метод: ${codeChallengeMethod})`);
        } else if (keycloak.authenticated) {

          setPkceInfo('PKCE!');
        }
      };

      checkPKCE();
    }
  }, [keycloak, initialized]);

  const [reportData, setReportData] = useState<any>(null);
  const [fromDate, setFromDate] = useState<string>('');
  const [toDate, setToDate] = useState<string>('');
  const [logoutLoading, setLogoutLoading] = useState(false);

  const downloadReport = async (e?: React.MouseEvent) => {
    if (e) {
      e.preventDefault();
      e.stopPropagation();
    }

    if (!keycloak?.authenticated) {
      setError('Not authenticated');
      return;
    }

    try {
      setLoading(true);
      setError(null);

      try {
        await keycloak.updateToken(30);
      } catch (tokenError) {
        setError('Failed to update token. Please try logging in again.');
        setLoading(false);
        return;
      }

      if (!keycloak.token) {
        setError('Failed to get token');
        setLoading(false);
        return;
      }

      let apiUrl = `${process.env.REACT_APP_API_URL}/reports`;
      const params = new URLSearchParams();

      if (fromDate) {
        params.append('from_date', fromDate);
      }
      if (toDate) {
        params.append('to_date', toDate);
      }

      if (params.toString()) {
        apiUrl += `?${params.toString()}`;
      }

      const response = await fetch(apiUrl, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${keycloak.token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        const errorText = await response.text();

        if (response.status === 401) {
          setError('Authentication failed. Please login again.');
          keycloak.logout();
          setLoading(false);
          return;
        }
        throw new Error(`HTTP error! status: ${response.status}, message: ${errorText}`);
      }

      const data = await response.json();
      setReportData(data);

    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = async () => {
    if (!keycloak) return;
    setLogoutLoading(true);
    try {
      await keycloak.logout();
    } finally {
      setLogoutLoading(false);
    }
  };

  if (!initialized) {
    return <div>Loading...</div>;
  }

  if (!keycloak.authenticated) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen bg-gray-100">
        <button
          onClick={() => keycloak.login()}
          className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
        >
          Login
        </button>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-gray-100">
      <div className="p-8 bg-white rounded-lg shadow-md max-w-2xl w-full">
        <h1 className="text-2xl font-bold mb-6">Usage Reports</h1>
        
        {pkceInfo && (
          <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded text-sm">
            <div className="font-semibold text-green-800 mb-1">PKCE Status:</div>
            <div className="text-green-700">{pkceInfo}</div>
          </div>
        )}

        <div className="mb-4 space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label htmlFor="from_date" className="block text-sm font-medium text-gray-700 mb-1">
                Дата начала (from_date):
              </label>
              <input
                type="date"
                id="from_date"
                value={fromDate}
                onChange={(e) => setFromDate(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
            <div>
              <label htmlFor="to_date" className="block text-sm font-medium text-gray-700 mb-1">
                Дата окончания (to_date):
              </label>
              <input
                type="date"
                id="to_date"
                value={toDate}
                onChange={(e) => setToDate(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
          </div>
          <div className="text-xs text-gray-500">
            Оставьте поля пустыми для автоматического выбора последних 7 дней
          </div>
        </div>

        <button
          type="button"
          onClick={(e) => downloadReport(e)}
          disabled={loading}
          className={`px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 ${
            loading ? 'opacity-50 cursor-not-allowed' : ''
          }`}
        >
          {loading ? 'Loading Report...' : 'Get Report'}
        </button>

        <button
          type="button"
          onClick={handleLogout}
          disabled={logoutLoading}
          className={`mt-3 px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600 ${
            logoutLoading ? 'opacity-50 cursor-not-allowed' : ''
          }`}
        >
          {logoutLoading ? 'Logging out...' : 'Logout'}
        </button>

        {error && (
          <div className="mt-4 p-4 bg-red-100 text-red-700 rounded border border-red-300">
            <div className="font-semibold mb-2">Ошибка:</div>
            <div>{error}</div>
          </div>
        )}

        {reportData && (
          <div className="mt-6 p-4 bg-gray-50 rounded-lg border border-gray-200">
            <h2 className="text-xl font-semibold mb-4">Report Data</h2>
            <div className="overflow-x-auto">
              <table className="min-w-full bg-white border border-gray-300 rounded-lg">
                <thead className="bg-gray-200">
                  <tr>
                    <th className="px-4 py-2 text-left border-b border-gray-300 font-semibold">Поле</th>
                    <th className="px-4 py-2 text-left border-b border-gray-300 font-semibold">Значение</th>
                  </tr>
                </thead>
                <tbody>
                  <tr className="hover:bg-gray-50">
                    <td className="px-4 py-2 border-b border-gray-200">Username</td>
                    <td className="px-4 py-2 border-b border-gray-200">{reportData.username}</td>
                  </tr>
                  <tr className="hover:bg-gray-50">
                    <td className="px-4 py-2 border-b border-gray-200">Total Usage</td>
                    <td className="px-4 py-2 border-b border-gray-200">{reportData.total_usage}</td>
                  </tr>
                  <tr className="hover:bg-gray-50">
                    <td className="px-4 py-2 border-b border-gray-200">Active Sessions</td>
                    <td className="px-4 py-2 border-b border-gray-200">{reportData.active_sessions}</td>
                  </tr>
                  {reportData.last_activity && (
                    <tr className="hover:bg-gray-50">
                      <td className="px-4 py-2 border-b border-gray-200">Last Activity</td>
                      <td className="px-4 py-2 border-b border-gray-200">
                        {new Date(reportData.last_activity).toLocaleString()}
                      </td>
                    </tr>
                  )}
                  {reportData.report_data && Object.keys(reportData.report_data).length > 0 && (
                    <>
                      {Object.entries(reportData.report_data).map(([key, value]) => {
                        if (key === 'message') return null;

                        let displayValue: string | number;
                        if (value === null || value === undefined) {
                          displayValue = '-';
                        } else if (typeof value === 'object' && value !== null) {
                          displayValue = JSON.stringify(value);
                        } else if (key.includes('date') || key.includes('ts') || key.includes('time')) {
                          try {
                            displayValue = new Date(value as string).toLocaleString();
                          } catch {
                            displayValue = String(value);
                          }
                        } else if (typeof value === 'number') {
                          displayValue = Number.isInteger(value) ? value : Number(value.toFixed(2));
                        } else {
                          displayValue = String(value);
                        }

                        const readableKey = key
                          .replace(/_/g, ' ')
                          .replace(/\b\w/g, l => l.toUpperCase());

                        return (
                          <tr key={key} className="hover:bg-gray-50">
                            <td className="px-4 py-2 border-b border-gray-200">{readableKey}</td>
                            <td className="px-4 py-2 border-b border-gray-200">{displayValue}</td>
                          </tr>
                        );
                      })}
                    </>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ReportPage;