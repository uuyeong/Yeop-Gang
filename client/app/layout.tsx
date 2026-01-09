import "./globals.css";
import type { Metadata } from "next";
import ClientLayout from "../components/ClientLayout";

export const metadata: Metadata = {
  title: "Yeop-Gang",
  description: "EBS 인강 AI 튜터",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ko">
      <body>
        <ClientLayout>{children}</ClientLayout>
      </body>
    </html>
  );
}

