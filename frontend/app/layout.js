import "./globals.css";

export const metadata = {
  title: "OmicsRoute — Evidence-aware bioinformatics workflow planning",
  description:
    "Plan context-specific bioinformatics workflows with dependency, constraint, compute-feasibility and evidence-aware decision support.",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
