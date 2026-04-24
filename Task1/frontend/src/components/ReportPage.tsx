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
          setPkceInfo(`✅ PKCE активен! code_challenge найден в URL (метод: ${codeChallengeMethod})`);
        } else if (keycloak.authenticated) {

          setPkceInfo('PKCE!');
        }
      };

      checkPKCE();
    }
  }, [keycloak, initialized]);

  const downloadReport = async () => {
    if (!keycloak?.token) {
      setError('Not authenticated');
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const response = await fetch(`${process.env.REACT_APP_API_URL}/reports`, {
        headers: {
          'Authorization': `Bearer ${keycloak.token}`
        }
      });

      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
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

        <button
          onClick={downloadReport}
          disabled={loading}
          className={`px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 ${
            loading ? 'opacity-50 cursor-not-allowed' : ''
          }`}
        >
          {loading ? 'Generating Report...' : 'Download Report'}
        </button>

        {error && (
          <div className="mt-4 p-4 bg-red-100 text-red-700 rounded">
            {error}
          </div>
        )}
      </div>
    </div>
  );
};

export default ReportPage;