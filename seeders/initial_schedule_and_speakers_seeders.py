from sqlalchemy.orm import Session
from models.Speaker import Speaker
from models.Schedule import Schedule
from datetime import datetime, timedelta
import random


def initial_speakers_seeders(db: Session, is_commit: bool = True):
    # generate seeders for speakers
    # Column Name 	Data Type 	Is Nullable 	Info
    # id 	UUID 	No
    # name 	VARCHAR 	No
    # bio 	TEXT 	Yes
    # photo_url 	VARCHAR 	Yes
    # email 	VARCHAR 	Yes
    # instagram_link 	VARCHAR 	Yes
    # x_link 	VARCHAR 	Yes
    # created_at 	TIMESTAMPTZ 	No
    # updated_at 	TIMESTAMPTZ 	No 	ketika create diisi value yang sama dengan created_at
    # is_keynote_speaker 	BOOL 	No 	default: false
    data = [
        {
            "name": f"Speaker {i}",
            "bio": f"Bio pembicara {i} yang sangat luar biasa dan inspiratif.",
            "photo_url": None,
            "email": f"speaker{i}@gmail.com",
            "instagram_link": f"https://instagram.com/speaker{i}",
            "x_link": f"https://x.com/speaker{i}",
        }
        for i in range(1, 11)
    ]
    for item in data:
        speaker = Speaker(**item)
        db.add(speaker)
    if is_commit:
        db.commit()
    print(f"Inserted {len(data)} speakers.")


def initial_schedules_seeders(db: Session, is_commit: bool = True):
    # Ambil semua speaker ID (UUID) yang sudah ada di DB
    speakers = db.query(Speaker.id).all()

    if not speakers:
        print("Tidak ada speaker di database. Tambahkan speaker terlebih dahulu.")
        return

    speaker_ids = [s.id for s in speakers]

    data = []
    for i in range(1, 11):
        # Pilih random speaker ID
        speaker_id = random.choice(speaker_ids)
        start_time = datetime.now() + timedelta(hours=i)
        end_time = start_time + timedelta(hours=1)

        data.append(
            {
                "topic": f"Topic {i}",
                "speaker_id": speaker_id,
                "description": f"Deskripsi untuk topik pembicaraan {i}.",
                "stream_link": f"https://youtube.com/{i}miau",
                "start": start_time,
                "end": end_time,
            }
        )

    for item in data:
        schedule = Schedule(**item)
        db.add(schedule)

    if is_commit:
        db.commit()

    print(f"✅ Inserted {len(data)} schedules.")
