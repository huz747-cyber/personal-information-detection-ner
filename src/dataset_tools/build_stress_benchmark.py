"""
Malaysian Open-Vocabulary Stress Benchmark Generator (Phase 6).

Constructs 200 fully annotated Malaysian sentences featuring 100% UNSEEN entities:
- 100 Dev partition sentences (data/stress_benchmark/dev.jsonl)
- 100 Test partition sentences (data/stress_benchmark/test.jsonl)
- Consolidated 200-sentence benchmark (data/stress_benchmark/malaysian_stress_200.jsonl)

Categories:
1. Standard Formal Bahasa Melayu (50 sentences total, 25 dev / 25 test)
2. Malaysian English (50 sentences total, 25 dev / 25 test)
3. Manglish & Conversational (40 sentences total, 20 dev / 20 test)
4. Malay-English Code-Switching (40 sentences total, 20 dev / 20 test)
5. Informal / Messaging (20 sentences total, 10 dev / 10 test)

Author: AI/ML Club
License: MIT
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple


def create_record(
    rec_id: str,
    text: str,
    entities: List[Dict[str, Any]],
    category: str,
    partition: str,
) -> Dict[str, Any]:
    """Helper to create a validated Doccano-compliant JSONL record."""
    labels = []
    for ent in entities:
        # Validate span matches exactly
        sub = text[ent["start"] : ent["end"]]
        assert sub == ent["text"], f"Span mismatch in {rec_id}: expected '{ent['text']}', got '{sub}'"
        labels.append([ent["start"], ent["end"], ent["label"]])

    return {
        "id": rec_id,
        "text": text,
        "label": labels,
        "metadata": {
            "category": category,
            "partition": partition,
            "language": category.split()[0],
            "unseen_guarantee": True,
            "phase": "Phase 6",
        },
    }


def generate_stress_data() -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    dev_records: List[Dict[str, Any]] = []
    test_records: List[Dict[str, Any]] = []

    # DEV ENTITY POOLS (100% unseen from training)
    dev_persons = [
        "Khairul Amri bin Jamaluddin", "Nur Farhana binti Mohamad Noor", "Tengku Adnan bin Tengku Mansor",
        "Zairil Khir bin Johari", "Tan Boon Heong", "Chong Wei Feng", "Lim Guan Seng", "Cheah Soon Kit",
        "Anand s/o Subramaniam", "Kavitha a/p Ramasamy", "Vimalraj a/l Murugan", "Thilagavathy a/p Govindasamy",
        "Stephen Kalong Ningkan", "Roland Sagah Wee Inn", "Christina Liew Chin Jin", "Baru Bian",
        "Syed Saddiq bin Syed Abdul Rahman", "Yeo Bee Yin", "Hannah Yeoh Tseow Suan", "Maszlee bin Malik",
        "Gobind Singh Deo a/l Karpal Singh", "Kasthuriraani a/p Patto", "Alexander Nanta Linggi",
        "Nancy binti Shukri", "Dzulkefly bin Ahmad"
    ]
    dev_orgs = [
        "Lembaga Kemajuan Ikan Malaysia", "Pihak Berkuasa Peranti Perubatan", "Perbadanan Harta Intelek Malaysia",
        "Institut Kefahaman Islam Malaysia", "Suruhanjaya Komunikasi dan Multimedia Malaysia",
        "Brahim's Holdings Berhad", "Padini Holdings Berhad", "Solarvest Holdings Berhad",
        "Farm Fresh Berhad", "Hartalega Holdings Berhad", "Majlis Bandaraya Iskandar Puteri",
        "Majlis Perbandaran Teluk Intan", "Universiti Malaysia Kelantan", "Universiti Sultan Zainal Abidin",
        "Nusantara BioTech Sdn Bhd", "Apex Logistics PLT", "Kencana Petroleum Berhad", "Frontken Corporation Berhad",
        "Kerjaya Prospek Group Berhad", "Genting Plantations Berhad", "Vortex Logistics PLT",
        "Mi Technovation Berhad", "Majlis Perbandaran Hang Tuah Jaya", "Universiti Teknikal Malaysia Melaka",
        "Kelington Group Berhad"
    ]
    dev_locs = [
        "Bagan Datuk", "Batu Gajah", "Tanjung Malim", "Pontian Kechil", "Changkat Jering", "Pantai Remis",
        "Kota Tinggi", "Banting", "Kuala Selangor", "Kuala Kubu Bharu", "Sungai Besar", "Gua Musang",
        "Pasir Mas", "Sungkai", "Jerantut", "Bentong", "Beaufort", "Keningau", "Lahad Datu",
        "Mukah", "Sarikei", "Kapit", "Sri Aman", "Limbang", "Lawas"
    ]

    # TEST ENTITY POOLS (100% unseen from training and dev)
    test_persons = [
        "Zulkifli bin Mohamad Al-Bakri", "Nurul Izzah binti Anwar", "Hishammuddin bin Hussein",
        "Wee Ka Siong", "Loke Siew Fook", "M. Kulasegaran a/l V. Murugeson", "Chow Kon Yeow",
        "Nga Kor Ming", "Sivakumar a/l Varatharaju Naidu", "Saravanan a/l Murugan", "Ewon Benedick",
        "Arthur Joseph Kurup", "Tiong King Sing", "Fadillah bin Yusof", "Mohamad bin Hasan",
        "Zambry bin Abd Kadir", "Shamsul Anuar bin Nasarah", "Sim Tze Tzin", "Chong Chieng Jen",
        "Pang Hok Liong", "Cha Kee Chin", "Khoo Poay Tiong", "Wong Shu Qi", "Teo Nie Ching",
        "Chua Tee Yong"
    ]
    test_orgs = [
        "Suruhanjaya Tenaga Malaysia", "Lembaga Lada Malaysia", "Perbadanan Produktiviti Malaysia",
        "Agensi Antidadah Kebangsaan", "Institut Penyelidikan Perhutanan Malaysia",
        "Econframe Berhad", "Coraza Integrated Technology Berhad", "TT Vision Holdings Berhad",
        "UWC Berhad", "Pentamaster Corporation Berhad", "Majlis Bandaraya Pasir Gudang",
        "Majlis Perbandaran Manjung", "Universiti Malaysia Pahang Al-Sultan Abdullah",
        "Universiti Malaysia Terengganu", "Borneo BioScience Sdn Bhd", "Zenith Engineering PLT",
        "Velesto Energy Berhad", "Dayang Enterprise Holdings Berhad", "Uzma Berhad",
        "Hibiscus Petroleum Berhad", "Yinson Holdings Berhad", "Binasat Communications Berhad",
        "Majlis Perbandaran Kulim", "Universiti Pertahanan Nasional Malaysia", "Aemulus Holdings Berhad"
    ]
    test_locs = [
        "Tangkak", "Mersing", "Simpang Renggam", "Yong Peng", "Labis", "Sitiawan", "Bagan Serai",
        "Grik", "Pengkalan Hulu", "Lenggong", "Kuala Kangsar", "Raub", "Kuala Lipis", "Maran",
        "Pekan", "Rompin", "Bachok", "Tumpat", "Pasir Puteh", "Machang", "Jeli", "Tanah Merah",
        "Besut", "Setiu", "Marang"
    ]

    # Synthesize Dev Records (100)
    # 1. Formal Malay (25)
    for i in range(25):
        p = dev_persons[i % len(dev_persons)]
        o = dev_orgs[i % len(dev_orgs)]
        l = dev_locs[i % len(dev_locs)]
        text = f"Menteri {o}, {p} telah mengadakan lawatan kerja rasmi ke {l} bagi meneliti pembangunan komuniti setempat."
        s_o = text.index(o)
        e_o = s_o + len(o)
        s_p = text.index(p)
        e_p = s_p + len(p)
        s_l = text.index(l)
        e_l = s_l + len(l)
        ents = [
            {"text": o, "label": "ORGANIZATION", "start": s_o, "end": e_o},
            {"text": p, "label": "PERSON", "start": s_p, "end": e_p},
            {"text": l, "label": "LOCATION", "start": s_l, "end": e_l},
        ]
        dev_records.append(create_record(f"stress-dev-malay-{i+1:03d}", text, ents, "Standard Formal Malay", "dev"))

    # 2. Malaysian English (25)
    for i in range(25):
        p = dev_persons[(i + 5) % len(dev_persons)]
        o = dev_orgs[(i + 7) % len(dev_orgs)]
        l = dev_locs[(i + 3) % len(dev_locs)]
        text = f"Senior director {p} from {o} announced a new regional logistics hub situated in {l} yesterday."
        s_p = text.index(p)
        e_p = s_p + len(p)
        s_o = text.index(o)
        e_o = s_o + len(o)
        s_l = text.index(l)
        e_l = s_l + len(l)
        ents = [
            {"text": p, "label": "PERSON", "start": s_p, "end": e_p},
            {"text": o, "label": "ORGANIZATION", "start": s_o, "end": e_o},
            {"text": l, "label": "LOCATION", "start": s_l, "end": e_l},
        ]
        dev_records.append(create_record(f"stress-dev-eng-{i+1:03d}", text, ents, "Malaysian English", "dev"))

    # 3. Manglish & Conversational (20)
    particles = ["lah", "meh", "lor", "leh", "one", "kan", "wei", "ya"]
    for i in range(20):
        p = dev_persons[(i + 2) % len(dev_persons)]
        o = dev_orgs[(i + 4) % len(dev_orgs)]
        l = dev_locs[(i + 6) % len(dev_locs)]
        part = particles[i % len(particles)]
        text = f"Aiyo, {p} already sent the contract to {o} branch in {l} {part}, don't need to panic so much!"
        s_p = text.index(p)
        e_p = s_p + len(p)
        s_o = text.index(o)
        e_o = s_o + len(o)
        s_l = text.index(l)
        e_l = s_l + len(l)
        ents = [
            {"text": p, "label": "PERSON", "start": s_p, "end": e_p},
            {"text": o, "label": "ORGANIZATION", "start": s_o, "end": e_o},
            {"text": l, "label": "LOCATION", "start": s_l, "end": e_l},
        ]
        dev_records.append(create_record(f"stress-dev-mang-{i+1:03d}", text, ents, "Manglish & Conversational", "dev"))

    # 4. Malay-English Code-Switching (20)
    for i in range(20):
        p = dev_persons[(i + 8) % len(dev_persons)]
        o = dev_orgs[(i + 3) % len(dev_orgs)]
        l = dev_locs[(i + 1) % len(dev_locs)]
        text = f"Semalam I jumpa {p} dekat {l}, dia cakap {o} tengah review tender perolehan tu."
        s_p = text.index(p)
        e_p = s_p + len(p)
        s_l = text.index(l)
        e_l = s_l + len(l)
        s_o = text.index(o)
        e_o = s_o + len(o)
        ents = [
            {"text": p, "label": "PERSON", "start": s_p, "end": e_p},
            {"text": l, "label": "LOCATION", "start": s_l, "end": e_l},
            {"text": o, "label": "ORGANIZATION", "start": s_o, "end": e_o},
        ]
        dev_records.append(create_record(f"stress-dev-cs-{i+1:03d}", text, ents, "Malay-English Code-Switching", "dev"))

    # 5. Informal / Messaging (10)
    for i in range(10):
        p = dev_persons[(i + 11) % len(dev_persons)]
        o = dev_orgs[(i + 9) % len(dev_orgs)]
        l = dev_locs[(i + 12) % len(dev_locs)]
        text = f"pls inform {p} dat {o} office at {l} is closed today for system maintenance tq"
        s_p = text.index(p)
        e_p = s_p + len(p)
        s_o = text.index(o)
        e_o = s_o + len(o)
        s_l = text.index(l)
        e_l = s_l + len(l)
        ents = [
            {"text": p, "label": "PERSON", "start": s_p, "end": e_p},
            {"text": o, "label": "ORGANIZATION", "start": s_o, "end": e_o},
            {"text": l, "label": "LOCATION", "start": s_l, "end": e_l},
        ]
        dev_records.append(create_record(f"stress-dev-msg-{i+1:03d}", text, ents, "Informal Messaging", "dev"))

    # Synthesize Test Records (100)
    # 1. Formal Malay (25)
    for i in range(25):
        p = test_persons[i % len(test_persons)]
        o = test_orgs[i % len(test_orgs)]
        l = test_locs[i % len(test_locs)]
        text = f"Pengarah {o}, {p} telah merasmikan bengkel kepimpinan belia di {l} pada pagi tadi."
        s_o = text.index(o)
        e_o = s_o + len(o)
        s_p = text.index(p)
        e_p = s_p + len(p)
        s_l = text.index(l)
        e_l = s_l + len(l)
        ents = [
            {"text": o, "label": "ORGANIZATION", "start": s_o, "end": e_o},
            {"text": p, "label": "PERSON", "start": s_p, "end": e_p},
            {"text": l, "label": "LOCATION", "start": s_l, "end": e_l},
        ]
        test_records.append(create_record(f"stress-test-malay-{i+1:03d}", text, ents, "Standard Formal Malay", "test"))

    # 2. Malaysian English (25)
    for i in range(25):
        p = test_persons[(i + 3) % len(test_persons)]
        o = test_orgs[(i + 6) % len(test_orgs)]
        l = test_locs[(i + 2) % len(test_locs)]
        text = f"According to chief representative {p}, {o} will expand operations into {l} starting next quarter."
        s_p = text.index(p)
        e_p = s_p + len(p)
        s_o = text.index(o)
        e_o = s_o + len(o)
        s_l = text.index(l)
        e_l = s_l + len(l)
        ents = [
            {"text": p, "label": "PERSON", "start": s_p, "end": e_p},
            {"text": o, "label": "ORGANIZATION", "start": s_o, "end": e_o},
            {"text": l, "label": "LOCATION", "start": s_l, "end": e_l},
        ]
        test_records.append(create_record(f"stress-test-eng-{i+1:03d}", text, ents, "Malaysian English", "test"))

    # 3. Manglish & Conversational (20)
    for i in range(20):
        p = test_persons[(i + 4) % len(test_persons)]
        o = test_orgs[(i + 8) % len(test_orgs)]
        l = test_locs[(i + 5) % len(test_locs)]
        part = particles[i % len(particles)]
        text = f"Better ask {p} about the {o} interview in {l} {part}, otherwise later miss the deadline!"
        s_p = text.index(p)
        e_p = s_p + len(p)
        s_o = text.index(o)
        e_o = s_o + len(o)
        s_l = text.index(l)
        e_l = s_l + len(l)
        ents = [
            {"text": p, "label": "PERSON", "start": s_p, "end": e_p},
            {"text": o, "label": "ORGANIZATION", "start": s_o, "end": e_o},
            {"text": l, "label": "LOCATION", "start": s_l, "end": e_l},
        ]
        test_records.append(create_record(f"stress-test-mang-{i+1:03d}", text, ents, "Manglish & Conversational", "test"))

    # 4. Malay-English Code-Switching (20)
    for i in range(20):
        p = test_persons[(i + 7) % len(test_persons)]
        o = test_orgs[(i + 1) % len(test_orgs)]
        l = test_locs[(i + 9) % len(test_locs)]
        text = f"You dah email {p} regarding projek {o} dekat area {l} ke belum?"
        s_p = text.index(p)
        e_p = s_p + len(p)
        s_o = text.index(o)
        e_o = s_o + len(o)
        s_l = text.index(l)
        e_l = s_l + len(l)
        ents = [
            {"text": p, "label": "PERSON", "start": s_p, "end": e_p},
            {"text": o, "label": "ORGANIZATION", "start": s_o, "end": e_o},
            {"text": l, "label": "LOCATION", "start": s_l, "end": e_l},
        ]
        test_records.append(create_record(f"stress-test-cs-{i+1:03d}", text, ents, "Malay-English Code-Switching", "test"))

    # 5. Informal / Messaging (10)
    for i in range(10):
        p = test_persons[(i + 10) % len(test_persons)]
        o = test_orgs[(i + 11) % len(test_orgs)]
        l = test_locs[(i + 10) % len(test_locs)]
        text = f"fyi {p} said {o} meeting in {l} postponed to next week ya"
        s_p = text.index(p)
        e_p = s_p + len(p)
        s_o = text.index(o)
        e_o = s_o + len(o)
        s_l = text.index(l)
        e_l = s_l + len(l)
        ents = [
            {"text": p, "label": "PERSON", "start": s_p, "end": e_p},
            {"text": o, "label": "ORGANIZATION", "start": s_o, "end": e_o},
            {"text": l, "label": "LOCATION", "start": s_l, "end": e_l},
        ]
        test_records.append(create_record(f"stress-test-msg-{i+1:03d}", text, ents, "Informal Messaging", "test"))

    return dev_records, test_records


def main() -> None:
    output_dir = Path("data/stress_benchmark")
    output_dir.mkdir(parents=True, exist_ok=True)

    dev_records, test_records = generate_stress_data()
    all_records = dev_records + test_records

    # Verify 100% unseen from commercial train
    with open("data/splits/commercial/train.jsonl", "r", encoding="utf-8") as f:
        train_recs = [json.loads(line) for line in f if line.strip()]

    train_entities: Set[str] = set()
    for r in train_recs:
        t = r["text"]
        for s, e, l in r.get("label", []):
            train_entities.add(t[s:e])

    benchmark_entities: Set[str] = set()
    for r in all_records:
        t = r["text"]
        for s, e, l in r.get("label", []):
            benchmark_entities.add(t[s:e])

    overlap = train_entities.intersection(benchmark_entities)
    assert len(overlap) == 0, f"FATAL: Entity overlap detected between stress benchmark and train: {overlap}"
    print(f"[+] Verified 100% unseen guarantee: 0 / {len(benchmark_entities)} entities overlap with training.")

    # Write JSONL partitions
    dev_path = output_dir / "dev.jsonl"
    test_path = output_dir / "test.jsonl"
    all_path = output_dir / "malaysian_stress_200.jsonl"

    def write_jsonl(path: Path, recs: List[Dict[str, Any]]) -> None:
        with open(path, "w", encoding="utf-8") as f:
            for r in recs:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        print(f"[+] Wrote {len(recs)} records to {path}")

    write_jsonl(dev_path, dev_records)
    write_jsonl(test_path, test_records)
    write_jsonl(all_path, all_records)


if __name__ == "__main__":
    from typing import Tuple
    main()
