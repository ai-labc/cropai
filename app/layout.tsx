import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'CropAgnoAI - Agriculture Analytics Dashboard',
  description: 'Visualize agriculture insights based on satellite imagery, weather data, and field boundaries',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ko">
      <body>{children}</body>
    </html>
  );
}

