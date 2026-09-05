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

def run_ict_ingestion_part3():
    init_db()
    print("=== Ingesting ICT Lectures 03 to 07 Study Materials ===")

    # 1. Ensure Subject exists
    subjects = {s["name"]: s["id"] for s in get_all_subjects()}
    ict_subject_name = "Information & Communication Technologies (ICT)"
    ict_subject_id = subjects.get(ict_subject_name)
    
    print(f"Subject '{ict_subject_name}' ID: {ict_subject_id}")

    # 2. Ingest Documents into RAG Knowledge Base
    docs_to_ingest = [
        {
            "filename": "ICT_Lecture_03_04_Digital_Divide_Computer_Generations_and_Input_Devices.txt",
            "doc_type": "Lecture Notes"
        },
        {
            "filename": "ICT_Lecture_05_Output_Devices_Memory_Hierarchy_and_Architecture.txt",
            "doc_type": "Lecture Notes"
        },
        {
            "filename": "ICT_Lecture_06_Communication_Systems_Modulation_Noise_and_Cellular_Tech.txt",
            "doc_type": "Lecture Notes"
        },
        {
            "filename": "ICT_Lecture_07_Satellite_Communication_GNSS_NavIC_and_GAGAN.txt",
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

    # 3. Create Test Set for Satellite & Cellular Communications
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, title FROM test_sets WHERE title LIKE '%Satellite & Mobile Communication%'")
    existing_tests = {r["title"]: r["id"] for r in cursor.fetchall()}
    conn.close()

    t_sat_title = "ICT: Satellite, Cellular & Mobile Communication Systems"
    if t_sat_title not in existing_tests:
        t_id = create_test_set(
            title=t_sat_title,
            subject_id=ict_subject_id,
            question_count=8,
            duration_minutes=20,
            description="Practice questions on NavIC (IRNSS), GAGAN SBAS, Satellite Orbits (GEO/LEO/MEO), Frequency Bands (Ka vs C-Band), Cellular Multiple Access (CDMA, OFDMA, NOMA), and Jitter."
        )

        q_list = [
            {
                "q": "What is the primary operational coverage area of India's indigenous NavIC (IRNSS) regional navigation satellite system?",
                "opts": ["Global coverage", "India and an extended area up to 1,500 km around Indian borders", "Only the Indian mainland", "Entire Asia-Pacific region"],
                "ans": "b",
                "exp": "NavIC / IRNSS consists of 7 operational satellites designed for India and an area extending up to 1500 km beyond its borders."
            },
            {
                "q": "India's GAGAN system, developed jointly by ISRO and AAI, is primarily categorized as what type of system?",
                "opts": ["Global Navigation Satellite System (GNSS)", "Satellite-Based Augmentation System (SBAS)", "Low Earth Orbit broadband constellation", "Mobile Satellite Service"],
                "ans": "b",
                "exp": "GAGAN (GPS Aided GEO Augmented Navigation) is a regional SBAS designed for precision civil aviation guidance."
            },
            {
                "q": "Which satellite communication frequency band provides high data rates with compact dish antennas but is severely vulnerable to rain fade and tropical attenuation?",
                "opts": ["L-Band (1-2 GHz)", "C-Band (4-8 GHz)", "Ka-Band (26-40 GHz)", "S-Band (2-4 GHz)"],
                "ans": "c",
                "exp": "Ka-band operates at 26-40 GHz, offering very high throughput and small spot beams, but suffers significant rain fade."
            },
            {
                "q": "In mobile and IP communications, which performance parameter measures the statistical variation in packet arrival delay and is most critical for real-time voice (VoIP) and video calls?",
                "opts": ["Bandwidth", "Latency", "Jitter", "Bit Error Rate (BER)"],
                "ans": "c",
                "exp": "Jitter is packet delay variation; high jitter causes buffer under-runs, resulting in choppy audio and video stutter in real-time streams."
            },
            {
                "q": "Which multiple access technique in 5G networks allows multiple users to share the same time and frequency resource blocks simultaneously by allocating distinct transmission power levels?",
                "opts": ["FDMA", "TDMA", "OFDMA", "NOMA (Non-Orthogonal Multiple Access)"],
                "ans": "d",
                "exp": "NOMA uses power-domain multiplexing and successive interference cancellation (SIC) at the receiver for high spectral efficiency."
            },
            {
                "q": "Why does an OLED display achieve perfect, infinite contrast ratio and true black levels compared to standard LCD displays?",
                "opts": ["It uses cold cathode fluorescent backlights", "It uses liquid crystals that rotate faster", "Each pixel is self-emissive and turns off completely with zero backlight leakage", "It uses blue laser illumination"],
                "ans": "c",
                "exp": "OLED pixels produce their own organic electroluminescence, allowing individual pixels to turn off entirely for true black."
            },
            {
                "q": "In computer memory architecture, Static RAM (SRAM) is preferred over Dynamic RAM (DRAM) for Cache memory primarily because:",
                "opts": ["SRAM is made of flip-flops and requires no periodic refreshing, making it much faster", "SRAM uses a single capacitor per bit and is cheaper", "SRAM is non-volatile", "SRAM has larger storage density per chip"],
                "ans": "a",
                "exp": "SRAM uses bistable latching flip-flops per bit, needing no refresh cycles and providing sub-nanosecond access speeds."
            },
            {
                "q": "The orbital altitude of a Geostationary Earth Orbit (GEO) satellite above the equator is approximately:",
                "opts": ["500 km", "2,000 km", "20,200 km", "35,786 km (~36,000 km)"],
                "ans": "d",
                "exp": "A GEO satellite orbits at ~35,786 km matching Earth's rotational period of 23h 56m 4s, making it appear stationary from ground."
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
        print(f"Created Test Set: '{t_sat_title}' with {len(q_list)} questions.")

    print("=== Ingestion of ICT Lectures 03-07 Completed! ===")

if __name__ == "__main__":
    run_ict_ingestion_part3()
