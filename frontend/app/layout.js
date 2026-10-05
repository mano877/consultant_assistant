import { Geist, Newsreader } from "next/font/google";
import "./globals.css";
import { ChatWidgetProvider } from "@/context/ChatWidgetContext";
const geistSans = Geist({ variable: "--font-geist-sans", subsets: ["latin"], display: "swap" });
const newsreader = Newsreader({ variable: "--font-editorial", subsets: ["latin"], style: ["normal", "italic"], display: "swap" });
export const metadata = {
  title: "GlobalPath Consulting | Your Study Journey, Thoughtfully Planned",
  description: "Personalised guidance for course selection, university applications and your journey to Australia. Explore your options with GlobalPath Consulting.",
};
export const viewport = { width: "device-width", initialScale: 1, interactiveWidget: "resizes-content" };
export default function RootLayout({ children }) {
  return <html lang="en" className={`${geistSans.variable} ${newsreader.variable}`}><body><ChatWidgetProvider>{children}</ChatWidgetProvider></body></html>;
}
