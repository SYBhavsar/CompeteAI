import type { Metadata } from "next";
import "./globals.css";
import { StoreProvider } from "@/lib/StoreProvider";
import { ThemeProvider } from "@/components/providers/theme-provider";
import { Toaster } from "react-hot-toast";

export const metadata: Metadata = {
  title: "AI Competitive Intelligence Platform",
  description: "Automated competitive intelligence with AI-powered insights",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="antialiased">
        <ThemeProvider
          attribute="class"
          defaultTheme="system"
          enableSystem
          disableTransitionOnChange
        >
          <StoreProvider>
            {children}
            <Toaster position="top-right" />
          </StoreProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
