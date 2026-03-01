import type { Metadata } from "next";
import localFont from "next/font/local";
import "./globals.css";
import { ToastProvider, Toaster } from "@/components/ui/toast";
import { AuthProvider } from "@/components/auth-provider";

const geistSans = localFont({
  src: "./fonts/GeistVF.woff",
  variable: "--font-sans",
  weight: "100 900",
});

const geistMono = localFont({
  src: "./fonts/GeistMonoVF.woff",
  variable: "--font-mono",
  weight: "100 900",
});

export const metadata: Metadata = {
  title: "ampere.capital | AI-Powered Trading Assistant",
  description: "AI-powered trading assistant for behavioral analysis and trade optimization",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className={`${geistSans.variable} ${geistMono.variable} bg-background text-foreground antialiased`}>
        <div className="min-h-screen bg-background">
          {/* Ambient background layers */}
          <div className="pointer-events-none fixed inset-0 overflow-hidden">
            {/* <div className="site-bg-gradient" aria-hidden="true" /> */}
            <div className="site-bg-rings" aria-hidden="true" />
            <div className="site-bg-vignette" aria-hidden="true" />
            <div className="site-bg-noise bg-noise-soft" aria-hidden="true" />
          </div>

          <div className="relative min-h-screen isolate">
            <AuthProvider>
              <ToastProvider>
                {children}
                <Toaster />
              </ToastProvider>
            </AuthProvider>
          </div>
        </div>
      </body>
    </html>
  );
}
