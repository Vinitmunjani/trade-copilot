import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { ToastProvider, ToastViewport } from "@/components/ui/toast";
import { AuthProvider } from "@/components/auth-provider";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Trade Co-Pilot | AI-Powered Trading Assistant",
  description: "AI-powered trading co-pilot for behavioral analysis and trade optimization",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className={`${inter.className} bg-slate-950 text-slate-100`}>
        <AuthProvider>
          <ToastProvider>
            {children}
            <ToastViewport />
          </ToastProvider>
        </AuthProvider>
      </body>
    </html>
  );
}
