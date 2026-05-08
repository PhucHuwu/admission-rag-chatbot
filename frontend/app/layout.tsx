import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Admission RAG Chatbot',
  description: 'Tra cứu và tư vấn tuyển sinh dựa trên dữ liệu đã crawl',
  icons: {
    icon: '/icon.svg',
    apple: '/apple-icon.svg',
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="vi">
      <body>{children}</body>
    </html>
  );
}
