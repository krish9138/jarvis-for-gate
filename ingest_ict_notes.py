import os
import sys
import json
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from database.connection import init_db, get_db_connection
from database.queries import (
    get_all_subjects, 
    add_subject, 
    get_all_documents,
    create_test_set,
    add_test_question
)
from services.rag_service import ingest_document

def run_ict_ingestion():
    init_db()
    print("=== Starting Ingestion of ESE/GATE ICT Study Materials ===")

    # 1. Ensure Subject exists
    subjects = {s["name"]: s["id"] for s in get_all_subjects()}
    ict_subject_name = "Information & Communication Technologies (ICT)"
    if ict_subject_name not in subjects:
        print(f"Adding Subject: '{ict_subject_name}'...")
        add_subject(ict_subject_name, category="ESE General Studies & ICT", target_hours=35.0)
        subjects = {s["name"]: s["id"] for s in get_all_subjects()}
    
    ict_subject_id = subjects.get(ict_subject_name)
    print(f"Subject '{ict_subject_name}' ID: {ict_subject_id}")

    # 2. Ingest Documents into RAG Knowledge Base
    docs_to_ingest = [
        {
            "filename": "ICT_Lecture_12_Advanced_Networking_Protocols_and_Wireless.txt",
            "doc_type": "Lecture Notes"
        },
        {
            "filename": "ICT_Lecture_13_Emerging_Network_Tech_Cloud_IoT_Web_Evolution.txt",
            "doc_type": "Lecture Notes"
        },
        {
            "filename": "ICT_Lecture_14_Network_Security_Cryptography_Digital_Signatures.txt",
            "doc_type": "Lecture Notes"
        },
        {
            "filename": "ICT_Lecture_15_Wireless_Web_Security_Malware_Cyber_Laws.txt",
            "doc_type": "Lecture Notes"
        },
        {
            "filename": "ICT_Lecture_16_E_Governance_India_Stack_Digital_India.txt",
            "doc_type": "Lecture Notes"
        }
    ]

    existing_docs = {d["original_name"]: d["id"] for d in get_all_documents()}

    for item in docs_to_ingest:
        fname = item["filename"]
        file_path = Path("data") / "documents" / fname
        if not file_path.exists():
            print(f"File not found: {file_path}")
            continue

        with open(file_path, "rb") as f:
            file_bytes = f.read()

        success, msg, doc_id = ingest_document(
            file_bytes=file_bytes,
            original_filename=fname,
            subject_id=ict_subject_id,
            doc_type=item["doc_type"]
        )
        print(f"[{'SUCCESS' if success else 'FAILED'}] {fname} -> {msg} (Doc ID: {doc_id})")

    # 3. Create Test Sets for ICT Practice
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, title FROM test_sets WHERE title LIKE '%ICT%'")
    existing_tests = {r["title"]: r["id"] for r in cursor.fetchall()}
    conn.close()

    # Lecture 12 Quiz
    t12_title = "ICT Lecture 12: Networking & Wireless Protocols"
    if t12_title not in existing_tests:
        t12_id = create_test_set(
            title=t12_title,
            subject_id=ict_subject_id,
            question_count=10,
            duration_minutes=20,
            description="Practice questions on IP (IPv4 vs IPv6), ICMP, ARP, DHCP, Email (SMTP, MIME, POP3, IMAP), Wi-Fi, WiMAX, Bluetooth, Zigbee, NFC, and FASTag RFID."
        )
        
        q12_list = [
            {
                "q": "A user with multiple devices (laptop, smartphone, tablet) wants to access their email such that any action (reading, deleting) on one device is reflected on all others. Which e-mail protocol is best suited for this requirement?",
                "opts": ["SMTP", "POP3", "IMAP", "MIME"],
                "ans": "c",
                "exp": "IMAP keeps email on the server and synchronizes state across multiple clients/devices, whereas POP3 downloads and deletes locally."
            },
            {
                "q": "What is the primary function of the Address Resolution Protocol (ARP) in a TCP/IP network?",
                "opts": ["To automatically assign IP addresses to newly connected hosts", "To report errors when an IP packet cannot be delivered", "To translate a known IP address into its corresponding physical (MAC) address", "To allow non-ASCII data to be transmitted over email"],
                "ans": "c",
                "exp": "ARP resolves network-layer logical IP addresses to data link layer physical MAC addresses."
            },
            {
                "q": "Which wireless technology is specifically designed with a mesh networking protocol to support low-power, low-cost, self-healing networks for IoT devices like smart bulbs and switches?",
                "opts": ["Wi-Fi", "Bluetooth", "WiMAX", "Zigbee"],
                "ans": "d",
                "exp": "Zigbee (IEEE 802.15.4) is designed for low-power, low-data-rate mesh networking in smart home and IoT systems."
            },
            {
                "q": "The FASTag system for automatic toll collection is a prominent application of which wireless technology?",
                "opts": ["Near Field Communication (NFC)", "Bluetooth Low Energy (BLE)", "Radio Frequency Identification (RFID)", "Worldwide Interoperability for Microwave Access (WiMAX)"],
                "ans": "c",
                "exp": "FASTag uses passive RFID technology mounted on the vehicle windshield for non-stop toll plaza authentication."
            },
            {
                "q": "A major limitation of IPv4, which necessitated the development of IPv6, was:",
                "opts": ["Its inability to handle real-time data", "Its inherently insecure design", "The eventual depletion of its 32-bit address space", "Its slow packet processing speed by routers"],
                "ans": "c",
                "exp": "IPv4 uses 32-bit addressing providing ~4.3 billion addresses, which faced exhaustion due to the exponential growth of internet devices."
            },
            {
                "q": "Consider the following statements regarding Wi-Fi and WiMAX:\n1. WiMAX operates over greater distances and supports more users than Wi-Fi.\n2. Wi-Fi is based on IEEE 802.16, while WiMAX is IEEE 802.11.\n3. The range of a WiMAX base station can be up to 50 km.\n4. Both Wi-Fi and WiMAX are primarily designed for short-range cable replacement.\nWhich of the above are correct?",
                "opts": ["1 and 3 only", "2 and 4 only", "1, 2 and 3 only", "1 and 4 only"],
                "ans": "a",
                "exp": "Wi-Fi is IEEE 802.11 (WLAN, ~100m); WiMAX is IEEE 802.16 (WMAN, up to 50 km)."
            },
            {
                "q": "Which of the following accurately describe Bluetooth technology?\n1. It is a high-power, long-range wireless standard.\n2. A Bluetooth network (Piconet) can have a maximum of 8 stations.\n3. It uses Frequency Hopping Spread Spectrum (FHSS).\n4. Bluetooth 5.0 offers longer range and faster speed.\nWhich of the above are correct?",
                "opts": ["1, 2 and 3 only", "2, 3 and 4 only", "1 and 4 only", "1, 2, 3 and 4"],
                "ans": "b",
                "exp": "Bluetooth is low-power short-range (PAN). A Piconet contains 1 master and up to 7 active slaves (max 8 stations)."
            },
            {
                "q": "Identify the correct statements about the various IP-related protocols:\n1. IPv6 uses a 128-bit address, whereas IPv4 uses a 32-bit address.\n2. DHCP is a protocol used to find the physical address when the Internet address is known.\n3. ICMP is used by hosts and routers to send error messages.\n4. ARP is a client-server application that delivers IP addresses to computers at first boot.\nWhich of the above are correct?",
                "opts": ["1 and 3 only", "2 and 4 only", "1, 2 and 3 only", "1, 3 and 4 only"],
                "ans": "a",
                "exp": "DHCP allocates IP addresses; ARP finds MAC addresses; ICMP sends error/diagnostic messages."
            },
            {
                "q": "Regarding Near Field Communication (NFC) and Radio Frequency Identification (RFID), which statements are correct?\n1. NFC is an offshoot of RFID technology.\n2. RFID tags are always active.\n3. NFC communication distance is typically greater than 1 meter.\n4. An NFC device can be either active (smartphone) or passive (tag).",
                "opts": ["1 and 4 only", "2 and 3 only", "1, 2 and 4 only", "3 and 4 only"],
                "ans": "a",
                "exp": "NFC operates at <20 cm (ultra-short range) based on 13.56 MHz RFID; RFID tags can be passive or active."
            },
            {
                "q": "Which of the following statements correctly differentiate between e-mail protocols?\n1. SMTP is a 'pull' protocol, while IMAP is a 'push' protocol.\n2. POP3 typically removes mail from the server after downloading it to a single client.\n3. MIME is a security protocol that encrypts email content.\n4. IMAP is designed to facilitate access to emails from multiple devices by keeping messages on the server.",
                "opts": ["1 and 3 only", "2 and 4 only", "1, 2 and 4 only", "2, 3 and 4 only"],
                "ans": "b",
                "exp": "SMTP is a push/sending protocol; POP3 downloads and removes; IMAP manages mail on server; MIME encodes non-ASCII multimedia."
            }
        ]

        for q in q12_list:
            add_test_question(
                test_set_id=t12_id,
                question_text=q["q"],
                options=q["opts"],
                correct_answer=q["ans"],
                explanation=q["exp"]
            )
        print(f"Created Test Set: '{t12_title}' with {len(q12_list)} questions.")

    # Lecture 15 Quiz
    t15_title = "ICT Lecture 15: Cyber Security, Malware & Cyber Laws"
    if t15_title not in existing_tests:
        t15_id = create_test_set(
            title=t15_title,
            subject_id=ict_subject_id,
            question_count=10,
            duration_minutes=20,
            description="Questions on WPA3, RSA, IT Act 2000, IT Amendment 2008, IPsec tunnel mode, ciphers, and digital signatures."
        )

        q15_list = [
            {
                "q": "A sender creates a unique, fixed-length fingerprint of a message and then encrypts this fingerprint with their private key. What is this encrypted fingerprint known as?",
                "opts": ["Ciphertext", "Digital Signature", "Public Key", "Authentication Header (AH)"],
                "ans": "b",
                "exp": "A digital signature is created by hashing the message and encrypting the digest using the sender's private key."
            },
            {
                "q": "Which wireless security protocol is considered the most secure modern standard, offering protection against offline dictionary attacks and supporting stronger encryption?",
                "opts": ["WEP", "WPA", "WPA2", "WPA3"],
                "ans": "d",
                "exp": "WPA3 uses Simultaneous Authentication of Equals (SAE) to protect against offline dictionary attacks."
            },
            {
                "q": "The RSA algorithm's security is fundamentally based on the computational difficulty of which mathematical problem?",
                "opts": ["Solving discrete logarithms", "Finding the inverse of a matrix", "Factoring large prime numbers", "Calculating the shortest path in a graph"],
                "ans": "c",
                "exp": "RSA security relies on the hardness of integer factorization of large composite numbers n = p * q."
            },
            {
                "q": "India's IT (Amendment) Act of 2008 introduced specific provisions and punishments for which of the following severe threats for the first time?",
                "opts": ["E-commerce fraud", "Data theft", "Cyber terrorism (Section 66F)", "Digital signature forgery"],
                "ans": "c",
                "exp": "Section 66F of the IT Amendment Act 2008 specifically introduced punishments up to life imprisonment for Cyber Terrorism."
            },
            {
                "q": "In IPsec, which mode encrypts the entire IP packet, including the header, and is commonly used to create VPNs?",
                "opts": ["Transport Mode", "Block Mode", "Tunnel Mode", "Stream Mode"],
                "ans": "c",
                "exp": "Tunnel mode encapsulates and encrypts the entire original IP packet and adds a new IP header."
            },
            {
                "q": "Digital Signatures provide which of the following security services?\n1. Authentication (proof of origin)\n2. Confidentiality (secrecy of the message)\n3. Integrity (proof that message was not altered)\n4. Non-Repudiation (sender cannot deny sending)",
                "opts": ["1, 3 and 4 only", "1 and 2 only", "2, 3 and 4 only", "1, 2, 3 and 4"],
                "ans": "a",
                "exp": "Digital signatures guarantee Authentication, Integrity, and Non-Repudiation. They do not by themselves encrypt the plaintext message for confidentiality."
            },
            {
                "q": "Assertion (A): The DES algorithm is no longer considered secure for modern applications.\nReason (R): Its key size of 56 bits is too small and vulnerable to brute-force attacks by modern computers.",
                "opts": ["Both A and R are true and R is the correct explanation of A", "Both A and R are true but R is NOT the correct explanation of A", "A is true but R is false", "A is false but R is true"],
                "ans": "a",
                "exp": "DES 56-bit keys can be cracked in hours with modern brute force, making AES the universal replacement."
            },
            {
                "q": "Assertion (A): Quantum Cryptography's security relies on the mathematical complexity of factoring large numbers.\nReason (R): The core principle of Quantum Cryptography is that the act of measuring a quantum particle, like a photon, inherently disturbs its state.",
                "opts": ["Both A and R are true and R is the correct explanation of A", "Both A and R are true but R is NOT the correct explanation of A", "A is true but R is false", "A is false but R is true"],
                "ans": "d",
                "exp": "Assertion is False because Quantum Cryptography relies on laws of physics (quantum mechanics), not mathematical complexity."
            }
        ]

        for q in q15_list:
            add_test_question(
                test_set_id=t15_id,
                question_text=q["q"],
                options=q["opts"],
                correct_answer=q["ans"],
                explanation=q["exp"]
            )
        print(f"Created Test Set: '{t15_title}' with {len(q15_list)} questions.")

    print("=== Ingestion and Indexing Completed Successfully! ===")

if __name__ == "__main__":
    run_ict_ingestion()
