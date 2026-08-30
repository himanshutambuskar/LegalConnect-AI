"""Static page content and structured data for Legal Connect."""

CATEGORIES = [
    {
        "id": "cybercrime",
        "name": "Cybercrime",
        "icon": "shield",
        "tagline": "Understand laws related to online fraud, harassment, and data protection.",
        "description": (
            "Understanding, preventing, and responding to digital offenses. "
            "Comprehensive guidance on legal recourse for online fraud, harassment, "
            "data breaches, and other cyber-related violations."
        ),
        "stepper_title": "Step-by-step: Filing a Cybercrime Complaint",
        "steps": [
            {
                "title": "Gather Evidence",
                "detail": "Save screenshots, emails, and transaction IDs before deleting anything.",
            },
            {
                "title": "File Online",
                "detail": "Register your complaint on the National Cyber Crime Reporting Portal.",
            },
            {
                "title": "Get Number",
                "detail": "Receive and save your unique acknowledgement number for tracking.",
            },
            {
                "title": "Follow Up",
                "detail": "Coordinate with local police if an FIR is required based on the complaint.",
            },
        ],
        "resources": [
            {
                "title": "National Cyber Crime Portal",
                "detail": "cybercrime.gov.in",
                "url": "https://cybercrime.gov.in",
                "icon": "globe",
            },
            {
                "title": "National Helpline",
                "detail": "Dial 1930 for financial fraud",
                "url": "tel:1930",
                "icon": "phone",
            },
            {
                "title": "IT Act Summary",
                "detail": "Key sections explained",
                "url": "https://www.indiacode.nic.in/handle/123456789/1999",
                "icon": "doc",
            },
        ],
        "ask_prompt": "What should I know about cybercrime and online fraud under Indian law?",
        "faqs": [
            {
                "q": "What constitutes financial cyber fraud?",
                "a": "Financial cyber fraud includes unauthorized UPI transfers, phishing, SIM-swap scams, fake customer-care calls, and other electronic theft of money or credentials.",
            },
            {
                "q": "How do I report online harassment?",
                "a": "Preserve screenshots and profile URLs, then report on cybercrime.gov.in. You may also approach the local cyber cell with the same evidence.",
            },
            {
                "q": "What is identity theft?",
                "a": "Identity theft is dishonest use of another person's unique identification feature, password, or electronic signature. Under the IT Act, it can attract imprisonment and a fine.",
            },
        ],
    },
    {
        "id": "fir-police",
        "name": "FIR & Police",
        "icon": "scales",
        "tagline": "Step-by-step guides on filing reports and your rights during police interactions.",
        "description": (
            "Guides on filing a First Information Report, Zero FIR, and citizen rights "
            "during police interaction, arrest, and follow-up under BNSS."
        ),
        "stepper_title": "Step-by-step: Filing a First Information Report (FIR)",
        "steps": [
            {
                "title": "Visit a Station",
                "detail": "Go to the station with jurisdiction, or any station for a Zero FIR.",
            },
            {
                "title": "State Facts Clearly",
                "detail": "Give date, time, place, and what happened, orally or in writing.",
            },
            {
                "title": "Verify & Sign",
                "detail": "Read the recorded FIR carefully before you sign it.",
            },
            {
                "title": "Obtain a Copy",
                "detail": "You are entitled to a free signed copy of the FIR under BNSS.",
            },
        ],
        "resources": [
            {
                "title": "BNSS / Criminal Procedure",
                "detail": "mha.gov.in",
                "url": "https://www.mha.gov.in/sites/default/files/250883_english_01042024.pdf",
                "icon": "doc",
            },
            {
                "title": "NCRB",
                "detail": "ncrb.gov.in",
                "url": "https://ncrb.gov.in",
                "icon": "globe",
            },
            {
                "title": "Emergency",
                "detail": "Dial 112",
                "url": "tel:112",
                "icon": "phone",
            },
        ],
        "ask_prompt": "When may police arrest without warrant under BNSS?",
        "faqs": [
            {
                "q": "What is a Zero FIR?",
                "a": "A Zero FIR can be registered at any police station, regardless of where the incident occurred, and is later transferred to the station with jurisdiction.",
            },
            {
                "q": "Can police refuse to register an FIR?",
                "a": "For cognizable offences, registration is mandatory. If refused, you can write to a senior police officer or approach a magistrate under BNSS.",
            },
            {
                "q": "Am I entitled to a free FIR copy?",
                "a": "Yes. The informant is entitled to a free copy of the registered FIR.",
            },
        ],
    },
    {
        "id": "consumer-rights",
        "name": "Consumer Rights",
        "icon": "cart",
        "tagline": "Recourse for faulty products, unfair trade practices, and service deficiencies.",
        "description": (
            "Recourse for faulty products, unfair trade practices, misleading advertisements, "
            "and service deficiencies under consumer protection law."
        ),
        "stepper_title": "Step-by-step: Lodging a Consumer Complaint",
        "steps": [
            {
                "title": "Issue Notice",
                "detail": "Write to the seller or service provider seeking repair, replacement, or refund.",
            },
            {
                "title": "Call 1915",
                "detail": "Register a grievance with the National Consumer Helpline.",
            },
            {
                "title": "File on E-Daakhil",
                "detail": "If unresolved, file online at edaakhil.nic.in.",
            },
            {
                "title": "Commission Hearing",
                "detail": "Attend mediation or the consumer commission hearing.",
            },
        ],
        "resources": [
            {
                "title": "National Consumer Helpline",
                "detail": "Dial 1915",
                "url": "tel:1915",
                "icon": "phone",
            },
            {
                "title": "E-Daakhil",
                "detail": "edaakhil.nic.in",
                "url": "https://edaakhil.nic.in",
                "icon": "globe",
            },
            {
                "title": "Consumer Protection Act, 2019",
                "detail": "Official statute",
                "url": "https://www.indiacode.nic.in/handle/123456789/15256",
                "icon": "doc",
            },
        ],
        "ask_prompt": "What rights do consumers have regarding defective products and unfair trade practices?",
        "faqs": [
            {
                "q": "Do I need a lawyer for a consumer complaint?",
                "a": "No. You can file and represent yourself, including through the E-Daakhil portal.",
            },
            {
                "q": "What is the helpline for consumer complaints?",
                "a": "You can call 1915 to reach the National Consumer Helpline.",
            },
        ],
    },
    {
        "id": "womens-safety",
        "name": "Women's Safety",
        "icon": "female",
        "tagline": "Legal provisions regarding harassment, domestic violence, and workplace safety.",
        "description": (
            "Legal provisions regarding harassment, domestic violence protection, workplace safety, "
            "and 24/7 emergency support helplines."
        ),
        "stepper_title": "Step-by-step: Seeking Protection Against Domestic Violence",
        "steps": [
            {
                "title": "Call 181",
                "detail": "Reach Women Helpline 181 or 112 for immediate help.",
            },
            {
                "title": "Protection Officer",
                "detail": "Contact the district Protection Officer or an authorised service provider.",
            },
            {
                "title": "Incident Report",
                "detail": "Prepare a Domestic Incident Report for submission.",
            },
            {
                "title": "Court Orders",
                "detail": "Apply for protection, residence, and monetary relief orders.",
            },
        ],
        "resources": [
            {
                "title": "Women Helpline",
                "detail": "Dial 181",
                "url": "tel:181",
                "icon": "phone",
            },
            {
                "title": "National Commission for Women",
                "detail": "ncw.nic.in",
                "url": "https://ncw.nic.in",
                "icon": "globe",
            },
            {
                "title": "PWDVA, 2005",
                "detail": "Protection of Women from Domestic Violence Act",
                "url": "https://www.indiacode.nic.in/handle/123456789/2021",
                "icon": "doc",
            },
        ],
        "ask_prompt": "What legal provisions exist under BNS and Indian law for women safety?",
        "faqs": [
            {
                "q": "Which emergency number can women in distress call?",
                "a": "Women in distress can call 181 for dedicated helpline support or 112 for national emergency services.",
            },
            {
                "q": "What legal relief is available against domestic violence?",
                "a": "Relief includes protection orders, residence orders, monetary relief, and custody orders under PWDVA.",
            },
        ],
    },
    {
        "id": "constitutional-rights",
        "name": "Constitutional Rights",
        "icon": "book",
        "tagline": "Fundamental rights, duties, and directive principles overview.",
        "description": (
            "Fundamental rights under the Constitution of India, fundamental duties, "
            "directive principles, and writ remedies."
        ),
        "stepper_title": "Step-by-step: Seeking a Constitutional Remedy",
        "steps": [
            {
                "title": "Identify Right",
                "detail": "Identify which fundamental or legal right is affected.",
            },
            {
                "title": "Collect Records",
                "detail": "Keep all notices, orders, and relevant correspondence.",
            },
            {
                "title": "Seek Legal Aid",
                "detail": "Contact NALSA or a qualified advocate if you need representation.",
            },
            {
                "title": "Approach Court",
                "detail": "File writ petitions before the High Court or Supreme Court as applicable.",
            },
        ],
        "resources": [
            {
                "title": "Constitution of India",
                "detail": "legislative.gov.in",
                "url": "https://legislative.gov.in/constitution-of-india",
                "icon": "doc",
            },
            {
                "title": "NALSA",
                "detail": "nalsa.gov.in",
                "url": "https://nalsa.gov.in",
                "icon": "globe",
            },
        ],
        "ask_prompt": "What fundamental rights does the Constitution of India guarantee to citizens?",
        "faqs": [
            {
                "q": "What is a writ petition?",
                "a": "A writ is a legal remedy issued by High Courts or the Supreme Court to enforce fundamental rights.",
            },
        ],
    },
    {
        "id": "traffic-rules",
        "name": "Traffic Rules",
        "icon": "car",
        "tagline": "Information on traffic violations, challans, and vehicle regulations.",
        "description": (
            "Information on traffic violations, e-challans, driving licences, "
            "and vehicle-related regulations."
        ),
        "stepper_title": "Step-by-step: Paying or Contesting an e-Challan",
        "steps": [
            {
                "title": "Check Status",
                "detail": "Look up the challan on the Parivahan e-challan portal.",
            },
            {
                "title": "Inspect Proof",
                "detail": "Review photos, time, place, and the section cited.",
            },
            {
                "title": "Pay Online",
                "detail": "If accepted, pay the fine online before the due date.",
            },
            {
                "title": "Contest",
                "detail": "Dispute through the virtual court option if issued incorrectly.",
            },
        ],
        "resources": [
            {
                "title": "e-Challan Portal",
                "detail": "echallan.parivahan.gov.in",
                "url": "https://echallan.parivahan.gov.in",
                "icon": "globe",
            },
            {
                "title": "MoRTH",
                "detail": "morth.nic.in",
                "url": "https://morth.nic.in",
                "icon": "globe",
            },
        ],
        "ask_prompt": "How do traffic challans and penalties work under Indian motor vehicle law?",
        "faqs": [
            {
                "q": "Where do I pay an e-challan?",
                "a": "You can pay online at echallan.parivahan.gov.in using your vehicle or challan number.",
            },
        ],
    },
]

CHAT_SIDEBAR_CATEGORIES = [
    {
        "id": "family-law",
        "name": "Family Law",
        "icon": "scales",
        "prompt": "What does Indian criminal law say about cruelty by a husband or relatives of a husband?",
    },
    {
        "id": "property-rights",
        "name": "Property Rights",
        "icon": "home",
        "prompt": "What offences relating to stolen property are covered in the Bharatiya Nyaya Sanhita?",
    },
    {
        "id": "employment",
        "name": "Employment",
        "icon": "briefcase",
        "prompt": "I was recently let go from my job without any prior warnings. They cited 'restructuring' but immediately hired someone else for my role. What are my rights regarding wrongful termination?",
    },
    {
        "id": "criminal-defense",
        "name": "Criminal Defense",
        "icon": "gavel",
        "prompt": "When may police arrest without warrant under BNSS?",
    },
    {
        "id": "contracts",
        "name": "Contracts",
        "icon": "doc",
        "prompt": "What does the Bharatiya Sakshya Adhiniyam say about electronic records as evidence?",
    },
    {
        "id": "consumer-protection",
        "name": "Consumer Protection",
        "icon": "shield",
        "prompt": "What is cheating under the Bharatiya Nyaya Sanhita?",
    },
]

STATUTES = [
    {
        "title": "Bharatiya Nyaya Sanhita, 2023",
        "detail": "Substantive criminal law replacing the Indian Penal Code for new cases.",
        "url": "https://bprd.nic.in/uploads/pdf/1706692028_eeccb6a2701f4c13ac9b.pdf",
    },
    {
        "title": "Bharatiya Nagarik Suraksha Sanhita, 2023",
        "detail": "Criminal procedure, including arrest, investigation, and trial process.",
        "url": "https://www.mha.gov.in/sites/default/files/250883_english_01042024.pdf",
    },
    {
        "title": "Bharatiya Sakshya Adhiniyam, 2023",
        "detail": "Law of evidence, including electronic records.",
        "url": "https://www.mha.gov.in/sites/default/files/250882_english_01042024.pdf",
    },
    {
        "title": "The Constitution of India",
        "detail": "Authentic text of the Constitution published by the Legislative Department.",
        "url": "https://legislative.gov.in/constitution-of-india",
    },
    {
        "title": "Information Technology Act, 2000",
        "detail": "Cyber offences, electronic records, and digital signatures.",
        "url": "https://www.meity.gov.in/content/information-technology-act-2000",
    },
    {
        "title": "Consumer Protection Act, 2019",
        "detail": "Consumer commissions, unfair trade practices, and product liability.",
        "url": "https://www.indiacode.nic.in/handle/123456789/15256",
    },
]

LEGAL_AID = [
    {
        "title": "National Legal Services Authority (NALSA)",
        "detail": "Free legal services for eligible persons and legal awareness programmes.",
        "url": "https://nalsa.gov.in",
    },
    {
        "title": "Legal Services Helpline",
        "detail": "Dial 15100 for legal services authority assistance.",
        "url": "tel:15100",
    },
    {
        "title": "eCourts Services",
        "detail": "Case status, cause lists, and orders across Indian courts.",
        "url": "https://ecourts.gov.in",
    },
    {
        "title": "Tele-Law",
        "detail": "Pre-litigation advice through the Department of Justice Tele-Law programme.",
        "url": "https://www.tele-law.in",
    },
]

SUGGESTED_QUESTIONS = [
    "How do I file an FIR?",
    "Tenant rights eviction",
    "Domestic violence help",
]


def get_category(category_id: str | None) -> dict:
    if not category_id:
        return CATEGORIES[0]
    for item in CATEGORIES:
        if item["id"] == category_id:
            return item
    return CATEGORIES[0]
