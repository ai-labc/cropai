/**
 * Error message component with retry functionality
 */

'use client';

import { useState } from 'react';

interface ErrorMessageProps {
  title?: string;
  message: string;
  details?: string;
  onRetry?: () => void;
  onDismiss?: () => void;
  retryable?: boolean;
  errorType?: 'network' | 'api' | 'timeout' | 'validation' | 'unknown';
}

export function ErrorMessage({
  title,
  message,
  details,
  onRetry,
  onDismiss,
  retryable = true,
  errorType = 'unknown',
}: ErrorMessageProps) {
  const [isRetrying, setIsRetrying] = useState(false);

  const handleRetry = async () => {
    if (!onRetry || isRetrying) return;
    
    setIsRetrying(true);
    try {
      await onRetry();
    } finally {
      setIsRetrying(false);
    }
  };

  // Error type specific icons and colors
  const errorConfig = {
    network: {
      icon: '🌐',
      bgColor: 'bg-red-50',
      borderColor: 'border-red-300',
      textColor: 'text-red-800',
      title: title || '네트워크 연결 오류',
    },
    api: {
      icon: '⚠️',
      bgColor: 'bg-orange-50',
      borderColor: 'border-orange-300',
      textColor: 'text-orange-800',
      title: title || 'API 오류',
    },
    timeout: {
      icon: '⏱️',
      bgColor: 'bg-yellow-50',
      borderColor: 'border-yellow-300',
      textColor: 'text-yellow-800',
      title: title || '요청 시간 초과',
    },
    validation: {
      icon: '📝',
      bgColor: 'bg-blue-50',
      borderColor: 'border-blue-300',
      textColor: 'text-blue-800',
      title: title || '입력 오류',
    },
    unknown: {
      icon: '❌',
      bgColor: 'bg-red-50',
      borderColor: 'border-red-300',
      textColor: 'text-red-800',
      title: title || '오류 발생',
    },
  };

  const config = errorConfig[errorType];

  return (
    <div className={`${config.bgColor} ${config.borderColor} border rounded-lg p-4 mb-4`}>
      <div className="flex items-start">
        <div className="flex-shrink-0 text-2xl mr-3">{config.icon}</div>
        <div className="flex-1">
          <h3 className={`${config.textColor} font-semibold mb-1`}>
            {config.title}
          </h3>
          <p className={`${config.textColor} text-sm mb-2`}>
            {message}
          </p>
          {details && (
            <details className="mb-2">
              <summary className={`${config.textColor} text-xs cursor-pointer hover:underline`}>
                자세한 정보 보기
              </summary>
              <pre className={`${config.textColor} text-xs mt-2 p-2 bg-white rounded overflow-auto max-h-32`}>
                {details}
              </pre>
            </details>
          )}
          <div className="flex gap-2 mt-3">
            {retryable && onRetry && (
              <button
                onClick={handleRetry}
                disabled={isRetrying}
                className={`px-3 py-1.5 text-sm font-medium rounded ${
                  isRetrying
                    ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                    : 'bg-blue-600 text-white hover:bg-blue-700'
                } transition-colors`}
              >
                {isRetrying ? (
                  <span className="flex items-center gap-1">
                    <svg className="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    재시도 중...
                  </span>
                ) : (
                  '재시도'
                )}
              </button>
            )}
            {onDismiss && (
              <button
                onClick={onDismiss}
                className="px-3 py-1.5 text-sm font-medium text-gray-700 bg-gray-200 rounded hover:bg-gray-300 transition-colors"
              >
                닫기
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

