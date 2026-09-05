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

def run_ict_ingestion_part2():
    init_db()
    print("=== Ingesting ICT Lectures 08 to 11 Study Materials ===")

    # 1. Ensure Subject exists
    subjects = {s["name"]: s["id"] for s in get_all_subjects()}
    ict_subject_name = "Information & Communication Technologies (ICT)"
    ict_subject_id = subjects.get(ict_subject_name)
    
    print(f"Subject '{ict_subject_name}' ID: {ict_subject_id}")

    # 2. Ingest Documents into RAG Knowledge Base
    docs_to_ingest = [
        {
            "filename": "ICT_Lecture_08_09_Network_History_Protocols_Media_and_Devices.txt",
            "doc_type": "Lecture Notes"
        },
        {
            "filename": "ICT_Lecture_10_11_Ethernet_Evolution_WAN_VPN_OSI_TCPIP_Models.txt",
            "doc_type": "Lecture Notes"
        }
    ]

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

    # 3. Create Test Set for OSI, TCP/IP & Network Fundamentals
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, title FROM test_sets WHERE title LIKE '%OSI & TCP/IP%'")
    existing_tests = {r["title"]: r["id"] for r in cursor.fetchall()}
    conn.close()

    t_osi_title = "ICT: OSI 7-Layer, TCP/IP & Network Fundamentals"
    if t_osi_title not in existing_tests:
        t_id = create_test_set(
            title=t_osi_title,
            subject_id=ict_subject_id,
            question_count=8,
            duration_minutes=20,
            description="Practice questions on ARPANET history, OSI layer functions, TCP vs UDP, Ethernet standards (10Base-T, 1000Base-LX), Network devices (Switch, Router, Hub), and Topologies."
        )

        q_list = [
            {
                "q": "Which OSI model layer is responsible for data format translation, syntax/semantics negotiation, data compression, and encryption/decryption?",
                "opts": ["Application Layer", "Presentation Layer", "Session Layer", "Transport Layer"],
                "ans": "b",
                "exp": "Presentation Layer (Layer 6) manages syntax, data formatting (ASCII/EBCDIC), compression, and cryptographic transformations."
            },
            {
                "q": "Why have modern high-speed computer interconnects (such as PCIe, SATA, USB 3.0) shifted from parallel transmission to serial transmission?",
                "opts": ["Serial cables are cheaper to manufacture", "Serial transmission eliminates signal attenuation", "Managing bit arrival synchronization across parallel wires (signal skew) becomes physically impossible at GHz clock frequencies", "Serial transmission does not require ground wires"],
                "ans": "c",
                "exp": "Clock skew and crosstalk across parallel lines limit max clock speed. Serial lines with embedded clocking achieve multi-gigahertz speeds."
            },
            {
                "q": "How many dedicated physical links are required to interconnect 'n' devices in a Full Mesh network topology?",
                "opts": ["n - 1", "n", "n(n - 1) / 2", "n(n + 1) / 2"],
                "ans": "c",
                "exp": "In a full mesh topology, every pair of nodes requires a point-to-point link: C(n, 2) = n(n-1)/2."
            },
            {
                "q": "A hospital needs a 1 Gbps high-speed backbone connection spanning 3 km across campus through an area with intense electromagnetic interference (EMI). Which Ethernet standard is most suitable?",
                "opts": ["1000Base-T", "1000Base-SX", "1000Base-LX", "10GBase-T"],
                "ans": "c",
                "exp": "1000Base-LX uses long-wavelength laser over single-mode optical fiber with maximum reach up to 5 km and total immunity to EMI."
            },
            {
                "q": "Which of the following statements about network layer devices is correct?",
                "opts": ["A Hub examines MAC addresses and forwards frames only to the target port", "A Switch operates at the Data Link layer and creates a separate collision domain for every port", "A Bridge operates at the Physical layer to amplify signals", "A Router forwards all broadcast traffic by default"],
                "ans": "b",
                "exp": "Switches operate at Layer 2, track MAC address tables, and isolate collision domains on each individual port."
            },
            {
                "q": "In a real-time video streaming application where minimizing latency is the top priority even if occasional frames are lost, which Transport Layer protocol is best suited?",
                "opts": ["TCP", "UDP", "IP", "HTTP"],
                "ans": "b",
                "exp": "UDP is connectionless and does not perform retransmission handshakes, avoiding playback buffering delays in live streaming."
            },
            {
                "q": "What was the initial packet-switching network protocol used by the 4 original nodes of ARPANET in 1969 before TCP/IP was adopted in 1983?",
                "opts": ["NCP (Network Control Protocol)", "IPX/SPX", "X.25", "HDLC"],
                "ans": "a",
                "exp": "ARPANET initially ran on NCP until January 1, 1983, when it officially migrated to the TCP/IP suite."
            },
            {
                "q": "The three essential elements that define any communication protocol are:",
                "opts": ["Syntax, Semantics, and Timing", "Source, Destination, and Medium", "Data, Header, and Trailer", "Frequency, Amplitude, and Phase"],
                "ans": "a",
                "exp": "A network protocol is formally defined by its Syntax (format/order), Semantics (meaning/action), and Timing (speed/sequencing)."
            }
        ]

        for q in q_list:
            add_test_question(
                test_set_id=t_id,
                question_text=q["q"],
                options=q["opts"],
                correct_answer=q["ans"],
                explanation=q["exp"]
            )
        print(f"Created Test Set: '{t_osi_title}' with {len(q_list)} questions.")

    print("=== Ingestion of ICT Lectures 08-11 Completed! ===")

if __name__ == "__main__":
    run_ict_ingestion_part2()
