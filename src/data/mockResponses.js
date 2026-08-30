export const CATEGORIES = [
  {
    id: "cybercrime",
    name: "Cybercrime",
    iconName: "Shield",
    tagline: "Online fraud, identity theft, harassment, and digital rights",
    description: "Understanding, preventing, and responding to digital offenses. Comprehensive guidance on legal recourse for online fraud, harassment, data breaches, and other cyber-related violations.",
    stepperTitle: "Step-by-step: Filing a Cybercrime Complaint",
    stepperSteps: [
      { step: 1, title: "Gather Evidence", description: "Save screenshots, emails, bank statements, and transaction IDs (UTR) before deleting anything." },
      { step: 2, title: "File Online", description: "Register your complaint on the National Cyber Crime Reporting Portal (cybercrime.gov.in) or call 1930." },
      { step: 3, title: "Get Number", description: "Receive and save your unique acknowledgement number for tracking your complaint status." },
      { step: 4, title: "Follow Up", description: "Coordinate with local police station Cyber Cell if an FIR is required based on financial threshold." }
    ],
    verifiedResources: [
      { title: "National Cyber Crime Portal", link: "https://cybercrime.gov.in", type: "Official Portal", desc: "Government gateway for lodging digital fraud & cybercrime complaints" },
      { title: "Financial Fraud Helpline (1930)", link: "tel:1930", type: "Helpline", desc: "Dial 1930 immediately to freeze fraudulent financial transactions" },
      { title: "Information Technology Act, 2000", link: "https://www.indiacode.nic.in/handle/123456789/1999", type: "Legal Statute", desc: "Key provisions: Sec 66C (Identity Theft), Sec 66D (Cheating by Personation)" }
    ]
  },
  {
    id: "fir-police",
    name: "FIR & Police",
    iconName: "FileText",
    tagline: "Police complaints, Zero FIR, bail rights, and police interactions",
    description: "Step-by-step guides on filing First Information Reports (FIR), understanding Zero FIR jurisdiction, bail procedures, and citizen rights during police interactions.",
    stepperTitle: "Step-by-step: Filing a First Information Report (FIR)",
    stepperSteps: [
      { step: 1, title: "Visit Police Station", description: "Go to the police station in whose jurisdiction the offense occurred (or any station for Zero FIR)." },
      { step: 2, title: "State Facts Clearly", description: "Provide details orally or in writing to the Duty Officer. Ensure accurate date, time, and incident description." },
      { step: 3, title: "Verify & Sign", description: "Read the written FIR carefully. Ensure no changes are made before signing your statement." },
      { step: 4, title: "Obtain Free Copy", description: "Under Section 154 CrPC / BNSS 2023, you are legally entitled to a free signed copy of the FIR immediately." }
    ],
    verifiedResources: [
      { title: "Bharatiya Nagarik Suraksha Sanhita (BNSS)", link: "https://www.mha.gov.in", type: "Legal Statute", desc: "Governs criminal procedure, FIR registration, and arrest rights in India" },
      { title: "Nyaaya Legal Information", link: "https://nyaaya.in", type: "Citizen Guide", desc: "Simplified guides on police complaint procedures and arrest rights" },
      { title: "National Crime Records Bureau", link: "https://ncrb.gov.in", type: "Government Portal", desc: "Official database and portal for crime statistics and online FIR lookup" }
    ]
  },
  {
    id: "consumer-rights",
    name: "Consumer Rights",
    iconName: "ShoppingCart",
    tagline: "Defective goods, service deficiency, misleading ads, and refunds",
    description: "Recourse for faulty products, unfair trade practices, misleading advertisements, and service deficiencies under the Consumer Protection Act, 2019.",
    stepperTitle: "Step-by-step: Lodging a Consumer Complaint",
    stepperSteps: [
      { step: 1, title: "Issue Notice", description: "Send a formal written notice or email to the seller/service provider demanding replacement or refund within 15 days." },
      { step: 2, title: "Call National Helpline", description: "Register an informal grievance at 1915 or online at consumerhelpline.gov.in." },
      { step: 3, title: "File on E-Daakhil", description: "If unresolved, submit a formal consumer case on the E-Daakhil portal (edaakhil.nic.in) without hiring a lawyer." },
      { step: 4, title: "Commission Hearing", description: "Attend District Consumer Redressal Commission hearing or mediation session for final order." }
    ],
    verifiedResources: [
      { title: "National Consumer Helpline (INGRAM)", link: "https://consumerhelpline.gov.in", type: "Official Helpline", desc: "Dial 1915 or log in to resolve complaints against brand/seller" },
      { title: "E-Daakhil Portal", link: "https://edaakhil.nic.in", type: "E-Filing Portal", desc: "File consumer dispute cases online with Consumer Commissions" },
      { title: "Consumer Protection Act, 2019", link: "https://consumeraffairs.nic.in", type: "Legal Statute", desc: "Establishes CCPA, e-commerce rules, and product liability provisions" }
    ]
  },
  {
    id: "womens-safety",
    name: "Women's Safety",
    iconName: "HeartHandshake",
    tagline: "Domestic violence, workplace POSH, stalking, and protection orders",
    description: "Legal provisions regarding harassment, domestic violence protection, POSH Act compliance at workplaces, and 24/7 emergency support helplines.",
    stepperTitle: "Step-by-step: Seeking Legal Protection Against Domestic Violence",
    stepperSteps: [
      { step: 1, title: "Call Helpline 181", description: "Reach out to Women Helpline 181 or 112 for immediate emergency response and shelter assistance." },
      { step: 2, title: "Contact Protection Officer", description: "Meet the designated District Protection Officer (DPO) or authorized NGO service provider." },
      { step: 3, title: "File DIR Report", description: "Prepare Domestic Incident Report (DIR) under Domestic Violence Act, 2005 for court magistrate." },
      { step: 4, title: "Obtain Court Orders", description: "Secure Protection Orders, Residence Orders, and monetary relief from Judicial Magistrate Court." }
    ],
    verifiedResources: [
      { title: "Women Helpline (181)", link: "tel:181", type: "Emergency Line", desc: "24/7 national emergency support line for women in distress" },
      { title: "National Commission for Women (NCW)", link: "https://ncw.nic.in", type: "Statutory Body", desc: "Online complaint portal for gender discrimination and safety complaints" },
      { title: "Protection of Women from Domestic Violence Act", link: "https://wcd.nic.in", type: "Legal Statute", desc: "Provides civil remedies including residence orders and financial maintenance" }
    ]
  },
  {
    id: "constitutional-rights",
    name: "Constitutional Rights",
    iconName: "BookOpen",
    tagline: "Fundamental rights, writs, freedom of speech, and legal remedies",
    description: "Fundamental rights under Part III of the Indian Constitution, citizen duties, directive principles, and writ remedies (Habeas Corpus, Mandamus, Certiorari).",
    stepperTitle: "Step-by-step: Filing a Writ Petition in High Court/Supreme Court",
    stepperSteps: [
      { step: 1, title: "Identify Violation", description: "Establish direct infringement of Fundamental Rights guaranteed under Articles 14 to 32." },
      { step: 2, title: "Consult Legal Counsel", description: "Draft petition through a registered High Court/Supreme Court Advocate or Legal Aid Counsel." },
      { step: 3, title: "File under Art 226/32", description: "Submit petition to High Court (Article 226) or Supreme Court (Article 32)." },
      { step: 4, title: "Court Hearing", description: "Present arguments for interim relief or issuance of extraordinary writ against state authorities." }
    ],
    verifiedResources: [
      { title: "Constitution of India (Legislative Dept)", link: "https://legislative.gov.in/constitution-of-india", type: "Official Text", desc: "Authentic text of the Constitution of India with amendments" },
      { title: "National Legal Services Authority (NALSA)", link: "https://nalsa.gov.in", type: "Legal Aid", desc: "Provides free legal services to eligible weaker sections of society" },
      { title: "eCourts Services Portal", link: "https://ecourts.gov.in", type: "Judicial Portal", desc: "Track court cases, orders, and judgment statuses across India" }
    ]
  },
  {
    id: "traffic-rules",
    name: "Traffic Rules",
    iconName: "Car",
    tagline: "e-Challans, drunk driving, license suspension, and vehicle inspection",
    description: "Information on Motor Vehicles Act amendments, fine structures, e-Challan payment and contestation, driving license rules, and traffic police inspection rights.",
    stepperTitle: "Step-by-step: Contesting or Paying an e-Challan",
    stepperSteps: [
      { step: 1, title: "Check Online Status", description: "Visit echallan.parivahan.gov.in or state traffic portal using Vehicle Number or DL Number." },
      { step: 2, title: "Inspect Proof", description: "Review photographic evidence, timestamp, and section mentioned on the challan." },
      { step: 3, title: "Pay Online", description: "If valid, pay fine online via secure payment gateway before due date to avoid Lok Adalat referral." },
      { step: 4, title: "Dispute in Virtual Court", description: "If contested, request referral to Virtual Court to present defense or dispute wrong violation." }
    ],
    verifiedResources: [
      { title: "Parivahan Sewa (e-Challan Portal)", link: "https://echallan.parivahan.gov.in", type: "Government Portal", desc: "Ministry of Road Transport portal for challan payment & license status" },
      { title: "Motor Vehicles (Amendment) Act 2019", link: "https://morth.nic.in", type: "Statutory Rules", desc: "Official penalties schedule for traffic violations across states" },
      { title: "Virtual Courts Portal", link: "https://vcourts.gov.in", type: "Judicial Service", desc: "Online adjudication portal for traffic challans without physical court visits" }
    ]
  }
];

export const MOCK_RESPONSES = [
  // CYBERCRIME
  {
    id: "cyber-1",
    category: "cybercrime",
    triggerPhrases: ["upi fraud", "online fraud", "money stolen", "phishing", "unauthorized transaction", "bank scam"],
    question: "I lost money in a UPI phishing fraud. What immediate steps should I take?",
    summary: "Immediate Recourse for Financial Cyber Fraud & UPI Scams",
    summaryText: "If you have lost money due to unauthorized UPI transfers or phishing, immediate action within the 'Golden Hour' (first 2 hours) is critical to freeze fraudulent accounts and recover funds under RBI guidelines.",
    steps: [
      { title: "Dial 1930 Immediately", detail: "Call the National Cyber Crime Financial Fraud Helpline 1930 to trigger instant account freezing across participating bank networks." },
      { title: "Notify Bank Fraud Cell", detail: "Inform your bank's 24/7 customer care within 3 days. Under RBI circulars, reporting within 3 days ensures zero liability for unauthorized electronic transactions." },
      { title: "Lodge Complaint on cybercrime.gov.in", detail: "File an official complaint on the National Cyber Crime Reporting Portal with transaction IDs (UTR), bank statement, and screenshot proof." },
      { title: "File Written Complaint at Local Cyber Cell", detail: "Submit a physical application along with your acknowledgement copy to the nearest police station Cyber Cell if amount exceeds ₹50,000." }
    ],
    sources: [
      { name: "National Cyber Crime Reporting Portal", url: "https://cybercrime.gov.in", excerpt: "Financial Fraud reporting system under MHA connected directly with 250+ banks, payment gateways, and UPI handles." },
      { name: "RBI Circular on Customer Protection (2017/2023)", url: "https://rbi.org.in", excerpt: "Customer liability is zero where fraud occurs due to bank deficiency or third-party breach reported within 3 working days." },
      { name: "IT Act, 2000 - Section 66D", url: "https://www.indiacode.nic.in", excerpt: "Punishment for cheating by personating by using computer resource: Imprisonment up to 3 years and fine up to ₹1 Lakh." }
    ],
    suggestedFollowups: [
      "What is the Golden Hour rule for UPI fraud?",
      "Can my bank refuse to refund unauthorized transaction money?",
      "How can I track the status of my 1930 complaint?"
    ]
  },
  {
    id: "cyber-2",
    category: "cybercrime",
    triggerPhrases: ["online harassment", "cyber stalking", "fake profile", "morphed photo", "blackmail"],
    question: "Someone created a fake profile and is blackmailing me with morphed photos online.",
    summary: "Legal Protections against Cyber Stalking and Digital Extortion",
    summaryText: "Online harassment, creation of fake profiles, and blackmailing using morphed images are severe criminal offenses under the Information Technology Act and Bharatiya Nyaya Sanhita (BNS).",
    steps: [
      { title: "Preserve All Digital Evidence", detail: "Take screenshots of profile URLs, chat history, mobile numbers, and messages before the attacker deletes them or deactivates the account." },
      { title: "Report Profile to Platform", detail: "Use the platform's 'Report Profile / Impersonation' feature to flag the malicious account for violation of community standards." },
      { title: "Lodge Complaint on cybercrime.gov.in", detail: "File a confidential complaint under 'Women / Child Related Crime' section on the National Cyber Crime Portal. You can file anonymously." },
      { title: "Approach Cyber Police Station", detail: "File an FIR under Section 66E (Privacy violation), Section 67 (Obscene content) of IT Act, and Section 354D of IPC / BNS." }
    ],
    sources: [
      { name: "IT Act 2000 - Section 66E & 67", url: "https://cybercrime.gov.in", excerpt: "Punishes violation of privacy and publishing obscene material in electronic form with imprisonment up to 5 years." },
      { name: "National Commission for Women Cyber Cell", url: "https://ncw.nic.in", excerpt: "Special helpline and digital portal dedicated to handling cyber harassment and revenge porn cases for women." }
    ],
    suggestedFollowups: [
      "Can I lodge a cyber harassment complaint anonymously?",
      "What legal actions can police take against fake social media accounts?",
      "How long does it take for platforms to remove morphed photos?"
    ]
  },
  {
    id: "cyber-3",
    category: "cybercrime",
    triggerPhrases: ["data breach", "identity theft", "aadhaar leak", "sim swap"],
    question: "My personal identity details and SIM card were fraudulently cloned (SIM Swap fraud). What are my rights?",
    summary: "Recourse for Identity Theft & SIM Swapping Offenses",
    summaryText: "SIM Swapping involves fraudulently transferring your mobile number to a new SIM card to intercept OTPs. This constitutes identity theft under IT Act Section 66C.",
    steps: [
      { title: "Contact Telecom Provider", detail: "Immediately call your mobile service operator to block the swapped SIM card and request subscriber verification audit." },
      { title: "Freeze Netbanking & Mobile Apps", detail: "Call all linked banks to halt netbanking and OTP-based transaction capabilities." },
      { title: "File Cyber Police FIR", detail: "Register a complaint for identity theft under Section 66C of IT Act 2000." },
      { title: "Report Telecom Negligence", detail: "Submit a complaint to Telecom Regulatory Authority of India (TRAI) if the operator issued a duplicate SIM without proper KYC check." }
    ],
    sources: [
      { name: "IT Act 2000 - Section 66C (Identity Theft)", url: "https://www.indiacode.nic.in", excerpt: "Whoever fraudulently or dishonestly makes use of the electronic signature or unique identification feature shall be punished." },
      { name: "DoT Telecom KYC Directives", url: "https://dot.gov.in", excerpt: "Strict mandatory physical/e-KYC verification required prior to issuing replacement SIM cards." }
    ],
    suggestedFollowups: [
      "How do I check how many SIM cards are issued in my name?",
      "Is telecom company liable for compensation in SIM swap fraud?",
      "What is the SANCHAR SAATHI portal?"
    ]
  },

  // FIR & POLICE
  {
    id: "fir-1",
    category: "fir-police",
    triggerPhrases: ["file fir", "how to file fir", "police refusal", "zero fir", "police station jurisdiction"],
    question: "How do I file an FIR and what can I do if the police refuse to register my FIR?",
    summary: "Procedure for Filing an FIR & Remedies for Police Refusal",
    summaryText: "Under Section 154 CrPC (BNSS 2023), police officers are legally mandated to register an FIR for cognizable offenses. Refusal to register an FIR is punishable under law.",
    steps: [
      { title: "Demand Registration under Cognizable Offense", detail: "Inform the Station House Officer (SHO) that your complaint involves a cognizable offense (theft, assault, fraud, etc.)." },
      { title: "Request Zero FIR if Outside Jurisdiction", detail: "If the crime occurred elsewhere, insist on registering a 'Zero FIR' which can be transferred to the concerned police station later." },
      { title: "Send Written Complaint to SP / Commissioner", detail: "If SHO refuses, send the written complaint via Registered Post to the Superintendent of Police (SP) or City Police Commissioner under Sec 154(3)." },
      { title: "Approach Judicial Magistrate Court", detail: "File an application under Section 156(3) CrPC / BNSS through a lawyer to get a direct judicial order compelling police to register FIR." }
    ],
    sources: [
      { name: "Lalita Kumari vs Govt of UP (Supreme Court 2014)", url: "https://sci.gov.in", excerpt: "5-Judge Constitutional Bench ruled that registration of FIR is mandatory if information discloses commission of cognizable offense." },
      { name: "Bharatiya Nagarik Suraksha Sanhita 2023 - Sec 173", url: "https://mha.gov.in", excerpt: "Mandates electronic filing of FIRs and provision of free FIR copy to informant." }
    ],
    suggestedFollowups: [
      "What is the difference between Zero FIR and regular FIR?",
      "Can I file an FIR online in India?",
      "What is Section 156(3) CrPC court direction?"
    ]
  },
  {
    id: "fir-2",
    category: "fir-police",
    triggerPhrases: ["arrest rights", "police detention", "handcuffing", "bail rights", "interrogation"],
    question: "What are my legal rights if I am stopped or arrested by the police?",
    summary: "Citizen Rights During Arrest, Detention & Police Interrogation",
    summaryText: "Article 22 of the Indian Constitution and Supreme Court DK Basu guidelines protect citizens against illegal arrest, harassment, and unauthorized detention.",
    steps: [
      { title: "Right to Know Grounds of Arrest", detail: "The arresting officer must immediately inform you of the exact legal charges and produce a valid arrest warrant (for non-cognizable offenses)." },
      { title: "Right to Inform Family / Lawyer", detail: "Police must immediately allow you to inform a relative, friend, or legal counsel of your choice regarding your detention location." },
      { title: "Right to Medical Examination", detail: "You have the legal right to be examined by a certified medical doctor every 48 hours to record physical condition and check for custodial abuse." },
      { title: "Production Before Magistrate within 24 Hours", detail: "Police cannot detain any arrested person beyond 24 hours without producing them before the nearest Judicial Magistrate." }
    ],
    sources: [
      { name: "DK Basu vs State of West Bengal (Supreme Court 1997)", url: "https://sci.gov.in", excerpt: "Established 11 mandatory procedural safeguards for police during arrest and detention to prevent custodial violence." },
      { name: "Article 22(1) & (2) - Constitution of India", url: "https://legislative.gov.in", excerpt: "Guarantees right to consult advocate of choice and mandatory magistrate production within 24 hours." }
    ],
    suggestedFollowups: [
      "Can female suspects be arrested at night by police?",
      "What is the process of getting anticipatory bail?",
      "When can police arrest without a warrant?"
    ]
  },

  // CONSUMER RIGHTS
  {
    id: "consumer-1",
    category: "consumer-rights",
    triggerPhrases: ["faulty product", "e-commerce refund", "defective item", "warranty dispute", "unfair practice"],
    question: "An e-commerce site delivered a damaged product and refused refund. What legal recourse do I have?",
    summary: "Consumer Rights & E-Commerce Refund Enforcement",
    summaryText: "Under the Consumer Protection (E-Commerce) Rules 2020, online platforms cannot refuse legitimate return or refund for damaged, defective, or spurious products.",
    steps: [
      { title: "Issue Formal Legal Notice / Email", detail: "Send a written email to the merchant's Grievance Officer clearly stating order ID, photos of defective product, and 7-day refund deadline." },
      { title: "Lodge Complaint on NCH Portal (1915)", detail: "Register a grievance on National Consumer Helpline (consumerhelpline.gov.in) or call 1915 for pre-litigation resolution." },
      { title: "File Case on E-Daakhil Portal", detail: "If merchant remains non-responsive, lodge an online case with the District Consumer Commission via edaakhil.nic.in." },
      { title: "Claim Compensation for Mental Agony", detail: "Request product cost refund plus interest and compensation for inconvenience under CPA 2019." }
    ],
    sources: [
      { name: "Consumer Protection (E-Commerce) Rules, 2020", url: "https://consumeraffairs.nic.in", excerpt: "Mandates appointment of Resident Grievance Officer and forbids cancellation charges on delayed deliveries." },
      { name: "Consumer Protection Act, 2019 - Sec 2(47)", url: "https://consumeraffairs.nic.in", excerpt: "Defines Unfair Trade Practice including refusal to take back defective goods or refund money." }
    ],
    suggestedFollowups: [
      "How much fee is required to file a consumer case on E-Daakhil?",
      "Can I claim compensation without hiring a lawyer?",
      "What is the time limit to file a consumer court case?"
    ]
  },
  {
    id: "consumer-2",
    category: "consumer-rights",
    triggerPhrases: ["service deficiency", "builder delay", "flight cancellation refund", "medical negligence"],
    question: "A service provider (flight/builder/hospital) failed to deliver promised service. How do I claim deficiency of service?",
    summary: "Legal Redressal for Deficiency of Service in India",
    summaryText: "Deficiency of service under Section 2(11) CPA 2019 covers any fault, imperfection, or inadequacy in quality, nature, and manner of performance.",
    steps: [
      { title: "Document Service Agreement & Defect Proof", detail: "Compile contract copies, invoices, email exchanges, tickets, and photos showing service default." },
      { title: "Send 15-Day Legal Notice", detail: "Draft and serve a legal demand notice seeking full refund along with compensation." },
      { title: "Approach Appropriate Consumer Commission", detail: "File case based on pecuniary jurisdiction: District (< ₹50 Lakhs), State (₹50 Lakhs to ₹2 Crores), National (> ₹2 Crores)." }
    ],
    sources: [
      { name: "Consumer Protection Act 2019 - Pecuniary Limits", url: "https://consumeraffairs.nic.in", excerpt: "Revised jurisdiction rules simplified filing based on actual consideration paid by consumer." }
    ],
    suggestedFollowups: [
      "Can I file a case against airlines for flight cancellation?",
      "What are real estate consumer rights under RERA vs Consumer Court?"
    ]
  },

  // WOMEN'S SAFETY
  {
    id: "women-1",
    category: "womens-safety",
    triggerPhrases: ["domestic violence", "husband abuse", "dowry harassment", "in-laws abuse", "shelter help"],
    question: "How can a victim seek immediate legal protection against domestic violence and abuse?",
    summary: "Protection Orders & Remedies under Domestic Violence Act 2005",
    summaryText: "The Protection of Women from Domestic Violence Act (PWDVA) 2005 provides comprehensive civil and emergency remedies for physical, emotional, sexual, or economic abuse.",
    steps: [
      { title: "Dial 181 or Emergency 112", detail: "Contact the 24/7 National Women Helpline 181 for immediate police dispatch, medical assistance, and shelter home placement." },
      { title: "Contact District Protection Officer (DPO)", detail: "Meet the government Protection Officer appointed in your district to record a Domestic Incident Report (DIR)." },
      { title: "Seek Emergency Court Orders", detail: "Apply before Judicial Magistrate for Protection Order (prohibiting abuser contact), Residence Order (right to reside in matrimonial home), and Maintenance." },
      { title: "File Criminal Complaint under BNS / IPC", detail: "Lodge FIR under Section 85/86 BNS (formerly Section 498A IPC) for cruelty and dowry harassment." }
    ],
    sources: [
      { name: "PWDV Act 2005 - Section 18 & 19", url: "https://wcd.nic.in", excerpt: "Grants interim protection orders and guarantees shared household residence rights irrespective of ownership." },
      { name: "Bharatiya Nyaya Sanhita 2023 - Sec 85 (498A)", url: "https://mha.gov.in", excerpt: "Cognizable offense punishable with up to 3 years imprisonment for husband or relatives subjecting woman to cruelty." }
    ],
    suggestedFollowups: [
      "Can a woman be evicted from her matrimonial home during dispute?",
      "What free legal aid is available for women under NALSA?",
      "How to contact local Protection Officers?"
    ]
  },
  {
    id: "women-2",
    category: "womens-safety",
    triggerPhrases: ["posh act", "workplace harassment", "sexual harassment office", "internal complaints committee"],
    question: "What legal protection exists for sexual harassment at the workplace (POSH Act)?",
    summary: "Workplace Sexual Harassment Protections & ICC Complaint Mechanism",
    summaryText: "The Sexual Harassment of Women at Workplace (Prevention, Prohibition and Redressal) Act, 2013 mandates every company with 10+ employees to constitute an Internal Complaints Committee (ICC).",
    steps: [
      { title: "Submit Written Complaint to ICC", detail: "File a written complaint to the company Internal Complaints Committee within 3 months of the incident." },
      { title: "Request Conciliation or Formal Inquiry", detail: "You may request informal conciliation or insist on a formal inquiry complete within 90 days." },
      { title: "Approach Local Complaints Committee (LCC)", detail: "If employer has fewer than 10 staff or complaint is against employer directly, file with District Collector's LCC." },
      { title: "Escalate to SESHebox / Police", detail: "Report on Ministry of WCD She-Box portal (shebox.nic.in) or file police FIR under BNS." }
    ],
    sources: [
      { name: "POSH Act, 2013 - Section 9 & 11", url: "https://wcd.nic.in", excerpt: "Mandates inquiry completion within 90 days and protects complainant against penal transfer or retaliation during inquiry." },
      { name: "SESHebox Portal (Ministry of WCD)", url: "https://shebox.nic.in", excerpt: "Single-window central monitoring portal for workplace sexual harassment complaints." }
    ],
    suggestedFollowups: [
      "What if my company does not have an ICC committee?",
      "Can remote/work-from-home harassment be covered under POSH?",
      "What interim relief can ICC recommend during inquiry?"
    ]
  },

  // CONSTITUTIONAL RIGHTS
  {
    id: "const-1",
    category: "constitutional-rights",
    triggerPhrases: ["fundamental rights", "habeas corpus", "right to equality", "freedom of speech", "writ petition"],
    question: "What are fundamental rights in India and how can I file a Writ Petition for rights violation?",
    summary: "Fundamental Rights & Constitutional Remedies under Articles 32 / 226",
    summaryText: "Part III of the Indian Constitution guarantees Fundamental Rights. Article 32 (Supreme Court) and Article 226 (High Courts) empower citizens to enforce rights via constitutional Writs.",
    steps: [
      { title: "Identify Affected Fundamental Right", detail: "Determine if government action violates Right to Equality (Art 14), Life & Liberty (Art 21), or Freedom of Speech (Art 19)." },
      { title: "Select Appropriate Writ Type", detail: "Habeas Corpus (unlawful detention), Mandamus (compel public duty), Certiorari / Prohibition (quash illegal administrative order)." },
      { title: "Draft Petition with Constitutional Lawyer", detail: "File Writ Petition directly in High Court (Art 226) or Supreme Court (Art 32) seeking immediate relief." },
      { title: "Apply for Free Legal Aid (NALSA)", detail: "If unable to afford counsel, apply at High Court Legal Services Committee for free senior advocacy representation." }
    ],
    sources: [
      { name: "Constitution of India - Article 32 & 226", url: "https://legislative.gov.in", excerpt: "Heart and soul of Constitution guaranteeing judicial review and enforcement of fundamental rights." },
      { name: "Puttaswamy Judgment (Supreme Court 2017)", url: "https://sci.gov.in", excerpt: "9-Judge Bench unanimously recognized Right to Privacy as intrinsic part of Right to Life under Article 21." }
    ],
    suggestedFollowups: [
      "What is Habeas Corpus and when is it used?",
      "Who is eligible for free legal aid under NALSA?",
      "What is the difference between Article 32 and Article 226?"
    ]
  },

  // TRAFFIC RULES
  {
    id: "traffic-1",
    category: "traffic-rules",
    triggerPhrases: ["traffic police rights", "challan dispute", "driving license check", "towing car", "drunk driving fine"],
    question: "What are my legal rights during traffic police checking, and how do I contest a wrong e-challan?",
    summary: "Traffic Police Inspection Guidelines & E-Challan Dispute Process",
    summaryText: "Under Motor Vehicles Act 2019, traffic police officers of specific ranks have clear limits on their power to inspect documents, seize licenses, or collect cash fines.",
    steps: [
      { title: "Check Officer Rank for Fine Collection", detail: "Only Sub-Inspector (SI) rank or above can issue fines on the spot. Constables cannot collect cash fines or take vehicle keys." },
      { title: "Digital Document Verification", detail: "You can legally produce driving license, RC, insurance, and PUC via Digilocker or mParivahan app under IT Act rules." },
      { title: "Never Hand Over Car Keys", detail: "Police officers cannot forcibly remove keys from your ignition or drag occupants out during routine checking." },
      { title: "Dispute Wrong Challan on Virtual Court", detail: "If issued an erroneous camera challan, visit echallan.parivahan.gov.in -> Dispute or contest in Virtual Court." }
    ],
    sources: [
      { name: "Motor Vehicles (Amendment) Act 2019", url: "https://morth.nic.in", excerpt: "Section 130 permits digital presentation of DL and registration certificates via DigiLocker." },
      { name: "Ministry of Road Transport Advisory 2018", url: "https://morth.nic.in", excerpt: "Directs all state police forces to honor digital documents and prohibits physical confiscation without cause." }
    ],
    suggestedFollowups: [
      "What is the fine for driving without a physical license?",
      "Can traffic police tow a car while someone is inside?",
      "How does Virtual Traffic Court work in India?"
    ]
  }
];

export const MOCK_FAQS = {
  cybercrime: [
    {
      q: "What constitutes financial cyber fraud in India?",
      a: "Financial cyber fraud includes unauthorized UPI transactions, SIM swap scams, phishing emails, fake customer care numbers, and investment app frauds where money is stolen using electronic means."
    },
    {
      q: "How do I report online harassment or cyber stalking?",
      a: "You can report cyber harassment anonymously or with identity on cybercrime.gov.in. Take screenshots of messages, profile URLs, and handle names prior to reporting."
    },
    {
      q: "What is identity theft under the IT Act?",
      a: "Under Section 66C of IT Act 2000, using another person's password, digital signature, Aadhaar, or electronic identifier fraudulently is identity theft, carrying up to 3 years imprisonment."
    },
    {
      q: "Is there a deadline to report online financial fraud to get my money back?",
      a: "Yes! Reporting within the 2-hour 'Golden Hour' via helpline 1930 increases chances of freezing funds. RBI guidelines grant zero liability if reported to bank within 3 working days."
    }
  ],
  "fir-police": [
    {
      q: "What is a Zero FIR and when can I use it?",
      a: "A Zero FIR can be registered at ANY police station regardless of where the incident occurred. The police station accepts the complaint, registers it under number '0', and transfers it to the jurisdiction station."
    },
    {
      q: "Can the police refuse to register an FIR?",
      a: "No. For cognizable offenses, registration of FIR is mandatory (Lalita Kumari ruling). If SHO refuses, you can send written complaint to SP or file under Sec 156(3) CrPC before a Magistrate."
    },
    {
      q: "Am I entitled to a free copy of the FIR?",
      a: "Yes! Under Section 154 CrPC / BNSS 2023, the informant or victim is legally entitled to receive a signed copy of the FIR immediately and completely free of cost."
    },
    {
      q: "Can a woman be arrested by police at night?",
      a: "Under Section 46(4) CrPC, no woman can be arrested after sunset and before sunrise, except under exceptional circumstances with prior written permission of a Judicial Magistrate."
    }
  ],
  "consumer-rights": [
    {
      q: "What is the fee required to file a case in Consumer Court?",
      a: "For claims up to ₹5 Lakhs on E-Daakhil, there is ZERO court fee! For higher amounts, nominal fees apply ranging from ₹200 to ₹500."
    },
    {
      q: "Do I need a lawyer to file a complaint in Consumer Commission?",
      a: "No lawyer is required. The Consumer Protection Act 2019 is designed for citizens to represent themselves or file online via edaakhil.nic.in directly."
    },
    {
      q: "What is the time limit to file a consumer complaint?",
      a: "You must file the complaint within 2 years from the date on which the cause of action (defect, refusal of refund, service failure) arose."
    },
    {
      q: "Are e-commerce platforms like Amazon or Flipkart liable for defective items?",
      a: "Yes. Under E-Commerce Rules 2020, marketplace platforms cannot disown responsibility and must resolve seller default, spurious products, and refund delays."
    }
  ],
  "womens-safety": [
    {
      q: "What emergency numbers can women call in India?",
      a: "Women can dial 181 (National Women Helpline) or 112 (All-in-one Emergency Response) for immediate police, medical, and shelter assistance 24/7."
    },
    {
      q: "What relief can a woman get under Domestic Violence Act 2005?",
      a: "Reliefs include Protection Orders (preventing violence), Residence Orders (right to live in home), Monetary Relief (monthly expenses), and Temporary Child Custody."
    },
    {
      q: "What is the POSH Act and ICC committee?",
      a: "POSH Act 2013 protects women at workplace. Every organization with 10+ employees must have an Internal Complaints Committee (ICC) headed by a senior woman employee."
    },
    {
      q: "Can a woman file a complaint for workplace harassment online?",
      a: "Yes! The Ministry of Women & Child Development runs the SESHebox portal (shebox.nic.in) for central registration and tracking of POSH complaints."
    }
  ],
  "constitutional-rights": [
    {
      q: "What is the difference between Article 32 and Article 226?",
      a: "Article 32 allows filing directly in Supreme Court for Fundamental Rights violations. Article 226 allows filing in High Courts for both Fundamental Rights AND statutory legal rights."
    },
    {
      q: "Who qualifies for free legal services in India?",
      a: "Under NALSA Act Section 12: women, children, SC/ST members, industrial workmen, victims of disaster/trauma, and individuals with annual income below specified state limit qualify for free lawyers."
    },
    {
      q: "What is Habeas Corpus writ?",
      a: "Habeas Corpus literally means 'produce the body'. It is a writ issued by court ordering police or authority to produce a detained person and justify lawful arrest."
    },
    {
      q: "Is Right to Privacy a Fundamental Right in India?",
      a: "Yes. In the historic Puttaswamy case (2017), Supreme Court declared Right to Privacy an intrinsic component of Right to Life & Personal Liberty under Article 21."
    }
  ],
  "traffic-rules": [
    {
      q: "Can a police constable take away my vehicle key or arrest me?",
      a: "No. Police constables cannot take ignition keys or collect cash fines. Only Sub-Inspector (SI) rank or above with designated e-challan machine can issue tickets."
    },
    {
      q: "Are digital documents in DigiLocker valid for traffic police?",
      a: "Yes! Under IT Act and MoRTH advisory, documents stored in DigiLocker or mParivahan apps are legally equivalent to original physical documents."
    },
    {
      q: "What happens if I don't pay an e-challan within the due date?",
      a: "Unpaid e-challans are forwarded to Virtual Courts or Lok Adalat, where you may receive a notice to pay fine or appear virtually before magistrate."
    },
    {
      q: "What is the penalty for drunk driving under revised rules?",
      a: "First offense incurs fine up to ₹10,000 and/or 6 months imprisonment. Subsequent offense incurs up to ₹15,000 fine and/or 2 years imprisonment."
    }
  ]
};

export const DEFAULT_FALLBACK_RESPONSE = {
  id: "fallback-default",
  category: "general",
  question: "General Legal Guidance",
  summary: "General Legal Guidance & Citizen Awareness",
  summaryText: "Legal Connect provides plain-language awareness grounded in Indian statutes. While your query didn't match a specific catalog entry, here are the standard procedural steps recommended for legal inquiries under Indian jurisdiction.",
  steps: [
    { title: "Identify Applicable Legal Sphere", detail: "Determine whether your matter falls under Criminal Law (BNS/CrPC), Civil Dispute, Consumer Redressal, or Constitutional Protection." },
    { title: "Gather Documentation & Evidence", detail: "Maintain chronological records of receipts, contracts, communication logs, notices, and photographic evidence." },
    { title: "Utilize Verified Government Helplines", detail: "Reach out to National Legal Services Authority (15100), Consumer Helpline (1915), Cyber Crime (1930), or Women Helpline (181)." },
    { title: "Seek Qualified Legal Representation", detail: "For formal court proceedings, consult a registered Bar Council advocate or visit your local District Legal Services Authority (DLSA) for free aid." }
  ],
  sources: [
    { name: "National Legal Services Authority (NALSA)", url: "https://nalsa.gov.in", excerpt: "Provides free and competent legal services to the weaker sections of society under Legal Services Authorities Act, 1987." },
    { name: "India Code Statutory Database", url: "https://www.indiacode.nic.in", excerpt: "Official digital repository of all Central and State Acts of Parliament in India." }
  ],
  suggestedFollowups: [
    "How can I access free legal aid from DLSA in my district?",
    "Where can I search official government laws online?",
    "How do I file a police complaint for financial fraud?"
  ]
};
