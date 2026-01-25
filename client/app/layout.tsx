import "./globals.css";
import type { Metadata } from "next";
import ClientLayout from "../components/ClientLayout";
import YeopgangHeader from "../components/YeopgangHeader";
import YeopgangFooter from "../components/YeopgangFooter";

export const metadata: Metadata = {
  title: "옆강",
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
        <ClientLayout>
          <div className="min-h-screen flex flex-col">
            <YeopgangHeader />
            <main className="flex-1">
              {children}
            </main>
            <YeopgangFooter />
          </div>
        </ClientLayout>
      </body>
    </html>
  );
}

