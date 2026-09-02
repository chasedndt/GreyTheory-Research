export const PUBLIC_INTELLIGENCE_SOURCES = [
  { id: "osv", name: "OSV.dev", use: "Package and dependency advisories", access: "Public API", posture: "Contract ready", endpoint: "api.osv.dev", mode: "CVE or package enrichment" },
  { id: "cisa-kev", name: "CISA KEV", use: "Known exploitation context", access: "Public JSON", posture: "Contract ready", endpoint: "cisa.gov", mode: "Prioritisation context" },
  { id: "epss", name: "FIRST EPSS", use: "Exploit-likelihood score and percentile", access: "Public API", posture: "Contract ready", endpoint: "api.first.org", mode: "CVE enrichment" },
  { id: "nvd", name: "NVD", use: "CVE, CVSS, CWE, and reference metadata", access: "Public API · optional key", posture: "Contract mapped", endpoint: "services.nvd.nist.gov", mode: "Vulnerability context" },
  { id: "github-advisories", name: "GitHub Advisories", use: "Global open-source security advisories", access: "REST API", posture: "Contract mapped", endpoint: "api.github.com", mode: "Advisory research" },
];

export const PROGRAMME_CONNECTORS = [
  { id: "hackerone", name: "HackerOne", access: "Programme API token", posture: "Not connected", safeUse: "Import programme and report data belonging to the authenticated account" },
  { id: "bugcrowd", name: "Bugcrowd", access: "User token + IP allowlist", posture: "Not connected", safeUse: "Import authorised programme scope and researcher workflow data" },
  { id: "intigriti", name: "Intigriti", access: "Account-approved integration", posture: "Discovery only", safeUse: "Future programme metadata import after official access is verified" },
];

export const INTEGRATION_GUARDRAILS = [
  "Read-only enrichment by default",
  "CVE or package identifiers only",
  "No hostname, target, scan, or exploit input",
  "Credentials remain outside the browser preview",
  "Every imported record keeps source and retrieval time",
  "External data informs research; it never proves a finding",
];
