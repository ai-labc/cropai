/**
 * Location Input component for latitude and longitude
 * Allows manual input and search for nearest farm
 */

'use client';

import { useState, useEffect } from 'react';

interface LocationValue {
  lat: number | null;
  lng: number | null;
}

interface LocationInputProps {
  value: LocationValue;
  onChange: (value: LocationValue) => void;
  onSearch: (lat: number, lng: number) => void;
  disabled?: boolean;
  searchResult?: {
    status: 'idle' | 'searching' | 'success' | 'not_found';
    message: string | null;
    distance: number | null;
  } | null;
}

export function LocationInput({ value, onChange, onSearch, disabled = false, searchResult = null }: LocationInputProps) {
  const [latInput, setLatInput] = useState<string>('');
  const [lngInput, setLngInput] = useState<string>('');
  const [errors, setErrors] = useState<{ lat?: string; lng?: string }>({});

  // Sync input with value prop
  useEffect(() => {
    if (value.lat !== null && value.lat !== undefined) {
      setLatInput(value.lat.toString());
    } else {
      setLatInput('');
    }
    if (value.lng !== null && value.lng !== undefined) {
      setLngInput(value.lng.toString());
    } else {
      setLngInput('');
    }
  }, [value]);

  const validateLat = (lat: string): boolean => {
    if (!lat.trim()) {
      setErrors(prev => ({ ...prev, lat: undefined }));
      return false;
    }
    const num = parseFloat(lat);
    if (isNaN(num)) {
      setErrors(prev => ({ ...prev, lat: 'Invalid latitude' }));
      return false;
    }
    if (num < -90 || num > 90) {
      setErrors(prev => ({ ...prev, lat: 'Latitude must be between -90 and 90' }));
      return false;
    }
    setErrors(prev => ({ ...prev, lat: undefined }));
    return true;
  };

  const validateLng = (lng: string): boolean => {
    if (!lng.trim()) {
      setErrors(prev => ({ ...prev, lng: undefined }));
      return false;
    }
    const num = parseFloat(lng);
    if (isNaN(num)) {
      setErrors(prev => ({ ...prev, lng: 'Invalid longitude' }));
      return false;
    }
    if (num < -180 || num > 180) {
      setErrors(prev => ({ ...prev, lng: 'Longitude must be between -180 and 180' }));
      return false;
    }
    setErrors(prev => ({ ...prev, lng: undefined }));
    return true;
  };

  const handleLatChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value;
    setLatInput(val);
    if (val.trim()) {
      validateLat(val);
      const num = parseFloat(val);
      if (!isNaN(num)) {
        onChange({ ...value, lat: num });
      }
    } else {
      onChange({ ...value, lat: null });
      setErrors(prev => ({ ...prev, lat: undefined }));
    }
  };

  const handleLngChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value;
    setLngInput(val);
    if (val.trim()) {
      validateLng(val);
      const num = parseFloat(val);
      if (!isNaN(num)) {
        onChange({ ...value, lng: num });
      }
    } else {
      onChange({ ...value, lng: null });
      setErrors(prev => ({ ...prev, lng: undefined }));
    }
  };

  const handleSearch = () => {
    const latValid = validateLat(latInput);
    const lngValid = validateLng(lngInput);

    if (latValid && lngValid && latInput.trim() && lngInput.trim()) {
      const lat = parseFloat(latInput);
      const lng = parseFloat(lngInput);
      onSearch(lat, lng);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  const canSearch = latInput.trim() !== '' && 
                    lngInput.trim() !== '' && 
                    !errors.lat && 
                    !errors.lng &&
                    parseFloat(latInput) >= -90 &&
                    parseFloat(latInput) <= 90 &&
                    parseFloat(lngInput) >= -180 &&
                    parseFloat(lngInput) <= 180;

  return (
    <div className="flex flex-col sm:flex-row items-start sm:items-center gap-2 w-full sm:w-auto">
      <div className="flex flex-col sm:flex-row items-start sm:items-center gap-2">
        <span className="text-white font-medium text-sm sm:text-base whitespace-nowrap">Lat:</span>
        <div className="flex flex-col">
          <input
            type="number"
            step="any"
            value={latInput}
            onChange={handleLatChange}
            onKeyPress={handleKeyPress}
            disabled={disabled}
            placeholder="Latitude"
            className="px-3 py-2 rounded-lg bg-white/10 border border-white/20 text-white placeholder-white/60 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:opacity-50 disabled:cursor-not-allowed w-full sm:w-32"
          />
          {errors.lat && (
            <span className="text-xs text-red-300 mt-1">{errors.lat}</span>
          )}
        </div>
      </div>
      <div className="flex flex-col sm:flex-row items-start sm:items-center gap-2">
        <span className="text-white font-medium text-sm sm:text-base whitespace-nowrap">Lon:</span>
        <div className="flex flex-col">
          <input
            type="number"
            step="any"
            value={lngInput}
            onChange={handleLngChange}
            onKeyPress={handleKeyPress}
            disabled={disabled}
            placeholder="Longitude"
            className="px-3 py-2 rounded-lg bg-white/10 border border-white/20 text-white placeholder-white/60 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:opacity-50 disabled:cursor-not-allowed w-full sm:w-32"
          />
          {errors.lng && (
            <span className="text-xs text-red-300 mt-1">{errors.lng}</span>
          )}
        </div>
      </div>
      <button
        onClick={handleSearch}
        disabled={!canSearch || disabled || searchResult?.status === 'searching'}
        className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap flex items-center gap-2"
      >
        {searchResult?.status === 'searching' ? (
          <>
            <svg className="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            Searching...
          </>
        ) : (
          'Search'
        )}
      </button>
    </div>
  );
}
