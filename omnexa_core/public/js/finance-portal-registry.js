frappe.provide('omnexa_finance');
omnexa_finance.PORTAL_REGISTRY = {
  "fe-servicing-portal": {
    "page": "fe-servicing-portal",
    "app": "omnexa_finance_engine",
    "sidebarRole": "executive",
    "titleAr": "FinanceCore — رحلة الخدمة",
    "titleEn": "FinanceCore — Servicing Journey",
    "roleAr": "مسؤول المحرك",
    "roleEn": "Engine Officer",
    "deskTitle": "FinanceCore — Servicing Journey"
  },
  "fe-executive-dashboard": {
    "page": "fe-executive-dashboard",
    "app": "omnexa_finance_engine",
    "sidebarRole": "executive",
    "titleAr": "FinanceCore — لوحة تنفيذية",
    "titleEn": "FinanceCore Executive",
    "roleAr": "مدير تنفيذي",
    "roleEn": "Group Executive",
    "deskTitle": "FinanceCore Executive"
  },
  "ce-servicing-portal": {
    "page": "ce-servicing-portal",
    "app": "omnexa_credit_engine",
    "sidebarRole": "credit",
    "titleAr": "CreditPulse — منشأة ائتمان",
    "titleEn": "Credit Origination Journey",
    "roleAr": "مسؤول ائتمان",
    "roleEn": "Credit Officer",
    "deskTitle": "Credit Origination Journey"
  },
  "ce-executive-dashboard": {
    "page": "ce-executive-dashboard",
    "app": "omnexa_credit_engine",
    "sidebarRole": "credit",
    "titleAr": "CreditPulse — تنفيذي",
    "titleEn": "CreditPulse Executive",
    "roleAr": "مدير ائتمان",
    "roleEn": "Credit Executive",
    "deskTitle": "CreditPulse Executive"
  },
  "rk-servicing-portal": {
    "page": "rk-servicing-portal",
    "app": "omnexa_credit_risk",
    "sidebarRole": "risk",
    "titleAr": "RiskGuard — تحليل مخاطر",
    "titleEn": "Credit Risk Analyst Journey",
    "roleAr": "محلل مخاطر",
    "roleEn": "Risk Analyst",
    "deskTitle": "Credit Risk Analyst Journey"
  },
  "rk-executive-dashboard": {
    "page": "rk-executive-dashboard",
    "app": "omnexa_credit_risk",
    "sidebarRole": "risk",
    "titleAr": "RiskGuard — تنفيذي",
    "titleEn": "RiskGuard Executive",
    "roleAr": "مدير مخاطر",
    "roleEn": "Risk Executive",
    "deskTitle": "RiskGuard Executive"
  },
  "al-servicing-portal": {
    "page": "al-servicing-portal",
    "app": "omnexa_alm",
    "sidebarRole": "treasury",
    "titleAr": "TreasuryALM — خزينة",
    "titleEn": "Treasury ALM Journey",
    "roleAr": "مسؤول خزينة",
    "roleEn": "Treasury Officer",
    "deskTitle": "Treasury ALM Journey"
  },
  "al-executive-dashboard": {
    "page": "al-executive-dashboard",
    "app": "omnexa_alm",
    "sidebarRole": "treasury",
    "titleAr": "TreasuryALM — تنفيذي",
    "titleEn": "TreasuryALM Executive",
    "roleAr": "مدير خزينة",
    "roleEn": "Treasury Executive",
    "deskTitle": "TreasuryALM Executive"
  },
  "cf-servicing-portal": {
    "page": "cf-servicing-portal",
    "app": "omnexa_consumer_finance",
    "sidebarRole": "consumer",
    "titleAr": "RetailLend — تمويل استهلاكي",
    "titleEn": "Consumer Lending Journey",
    "roleAr": "مسؤول تمويل استهلاكي",
    "roleEn": "Consumer Officer",
    "deskTitle": "Consumer Lending Journey"
  },
  "cf-executive-dashboard": {
    "page": "cf-executive-dashboard",
    "app": "omnexa_consumer_finance",
    "sidebarRole": "consumer",
    "titleAr": "RetailLend — تنفيذي",
    "titleEn": "RetailLend Executive",
    "roleAr": "مدير تجزئة",
    "roleEn": "Retail Executive",
    "deskTitle": "RetailLend Executive"
  },
  "vf-servicing-portal": {
    "page": "vf-servicing-portal",
    "app": "omnexa_vehicle_finance",
    "sidebarRole": "auto",
    "titleAr": "AutoLend — تمويل مركبات",
    "titleEn": "Auto Finance Journey",
    "roleAr": "مسؤول مركبات",
    "roleEn": "Auto Officer",
    "deskTitle": "Auto Finance Journey"
  },
  "vf-executive-dashboard": {
    "page": "vf-executive-dashboard",
    "app": "omnexa_vehicle_finance",
    "sidebarRole": "auto",
    "titleAr": "AutoLend — تنفيذي",
    "titleEn": "AutoLend Executive",
    "roleAr": "مدير مركبات",
    "roleEn": "Auto Executive",
    "deskTitle": "AutoLend Executive"
  },
  "mg-servicing-portal": {
    "page": "mg-servicing-portal",
    "app": "omnexa_mortgage_finance",
    "sidebarRole": "mortgage",
    "titleAr": "HomeLend — رهن عقاري",
    "titleEn": "Mortgage Journey",
    "roleAr": "مسؤول رهن",
    "roleEn": "Mortgage Officer",
    "deskTitle": "Mortgage Journey"
  },
  "mg-executive-dashboard": {
    "page": "mg-executive-dashboard",
    "app": "omnexa_mortgage_finance",
    "sidebarRole": "mortgage",
    "titleAr": "HomeLend — تنفيذي",
    "titleEn": "HomeLend Executive",
    "roleAr": "مدير رهن",
    "roleEn": "Mortgage Executive",
    "deskTitle": "HomeLend Executive"
  },
  "fc-servicing-portal": {
    "page": "fc-servicing-portal",
    "app": "omnexa_factoring",
    "sidebarRole": "factoring",
    "titleAr": "FactorFlow — تخصيم",
    "titleEn": "Factoring Journey",
    "roleAr": "مسؤول تخصيم",
    "roleEn": "Factoring Officer",
    "deskTitle": "Factoring Journey"
  },
  "fc-executive-dashboard": {
    "page": "fc-executive-dashboard",
    "app": "omnexa_factoring",
    "sidebarRole": "factoring",
    "titleAr": "FactorFlow — تنفيذي",
    "titleEn": "FactorFlow Executive",
    "roleAr": "مدير تخصيم",
    "roleEn": "Factoring Executive",
    "deskTitle": "FactorFlow Executive"
  },
  "sr-servicing-portal": {
    "page": "sr-servicing-portal",
    "app": "omnexa_sme_retail_finance",
    "sidebarRole": "sme",
    "titleAr": "SMECapital — تمويل منشآت",
    "titleEn": "SME Finance Journey",
    "roleAr": "مسؤول منشآت",
    "roleEn": "SME Officer",
    "deskTitle": "SME Finance Journey"
  },
  "sr-executive-dashboard": {
    "page": "sr-executive-dashboard",
    "app": "omnexa_sme_retail_finance",
    "sidebarRole": "sme",
    "titleAr": "SMECapital — تنفيذي",
    "titleEn": "SMECapital Executive",
    "roleAr": "مدير منشآت",
    "roleEn": "SME Executive",
    "deskTitle": "SMECapital Executive"
  },
  "mf-servicing-portal": {
    "page": "mf-servicing-portal",
    "app": "omnexa_sme_microfinance",
    "sidebarRole": "micro",
    "titleAr": "MicroCapital — ميداني",
    "titleEn": "Microfinance Field Journey",
    "roleAr": "مسؤول ميداني",
    "roleEn": "Field Officer",
    "deskTitle": "Microfinance Field Journey"
  },
  "mf-executive-dashboard": {
    "page": "mf-executive-dashboard",
    "app": "omnexa_sme_microfinance",
    "sidebarRole": "micro",
    "titleAr": "MicroCapital — تنفيذي",
    "titleEn": "MicroCapital Executive",
    "roleAr": "مدير مicrofinance",
    "roleEn": "Micro Executive",
    "deskTitle": "MicroCapital Executive"
  },
  "lf-servicing-portal": {
    "page": "lf-servicing-portal",
    "app": "omnexa_leasing_finance",
    "sidebarRole": "leasing",
    "titleAr": "LeaseMaster — تأجير",
    "titleEn": "Leasing Journey",
    "roleAr": "مسؤول تأجير",
    "roleEn": "Leasing Officer",
    "deskTitle": "Leasing Journey"
  },
  "lf-executive-dashboard": {
    "page": "lf-executive-dashboard",
    "app": "omnexa_leasing_finance",
    "sidebarRole": "leasing",
    "titleAr": "LeaseMaster — تنفيذي",
    "titleEn": "LeaseMaster Executive",
    "roleAr": "مدير تأجير",
    "roleEn": "Leasing Executive",
    "deskTitle": "LeaseMaster Executive"
  },
  "or-grc-portal": {
    "page": "or-grc-portal",
    "app": "omnexa_operational_risk",
    "sidebarRole": "grc",
    "titleAr": "OpRisk — حوكمة GRC",
    "titleEn": "Operational Risk GRC Journey",
    "roleAr": "مسؤول GRC",
    "roleEn": "GRC Officer",
    "deskTitle": "Operational Risk GRC Journey"
  },
  "or-executive-dashboard": {
    "page": "or-executive-dashboard",
    "app": "omnexa_operational_risk",
    "sidebarRole": "grc",
    "titleAr": "OpRisk — تنفيذي",
    "titleEn": "OpRisk Executive",
    "roleAr": "مدير مخاطر تشغيلية",
    "roleEn": "OpRisk Executive",
    "deskTitle": "OpRisk Executive"
  },
  "acct-executive-dashboard": {
    "page": "acct-executive-dashboard",
    "app": "omnexa_accounting",
    "sidebarRole": "accounting",
    "titleAr": "FinTruth — لوحة تنفيذية",
    "titleEn": "FinTruth Executive",
    "roleAr": "مراقب محاسبي",
    "roleEn": "Accounting Controller",
    "deskTitle": "FinTruth Executive"
  },
  "accounting-close-dashboard": {
    "page": "accounting-close-dashboard",
    "app": "omnexa_accounting",
    "sidebarRole": "accounting",
    "titleAr": "FinTruth — إغلاق محاسبي",
    "titleEn": "Accounting Close Journey",
    "roleAr": "مسؤول إغلاق",
    "roleEn": "Close Officer",
    "deskTitle": "Accounting Close Journey"
  }
};
