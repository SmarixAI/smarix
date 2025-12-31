import '@/components/admin/globals.css';
import { AuthProvider } from '@/components/auth/AuthContext';
import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Smarix AI',
  description: 'AI based data retention and knowledge transfer',
  icons: {
    icon: '/logo.png', 
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <AuthProvider>
          {children}
        </AuthProvider>
      </body>
    </html>
  );
}

