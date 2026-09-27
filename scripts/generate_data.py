from pathlib import Path
import pandas as pd

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
DATA_DIR.mkdir(exist_ok=True)

hotels = pd.DataFrame([
    ["H001", "Stockholm Central", "Stockholm", "2026-09-01 08:00:00"],
    ["H002", "Gothenburg Riverside", "Gothenburg", "2026-09-01 08:00:00"],
    ["H003", "Malmo City", "Malmo", "2026-09-01 08:00:00"],
], columns=["hotel_id", "hotel_name", "city", "source_updated_at"])

bookings = pd.DataFrame([
    ["B001", "H001", "G001", "2026-09-01", "2026-09-10", "2026-09-12", "CONFIRMED", "2026-09-01 10:00:00"],
    ["B002", "H001", "G002", "2026-09-01", "2026-09-11", "2026-09-14", "CANCELLED", "2026-09-01 11:00:00"],
    ["B003", "H002", "G003", "2026-09-01", "2026-09-08", "2026-09-09", "CONFIRMED", "2026-09-01 12:00:00"],
    # Late-arriving update: same booking, newer source timestamp.
    ["B001", "H001", "G001", "2026-09-01", "2026-09-10", "2026-09-12", "CANCELLED", "2026-09-01 15:00:00"],
    # Invalid foreign key: H999 does not exist in hotels.
    ["B004", "H999", "G004", "2026-09-02", "2026-09-10", "2026-09-12", "CONFIRMED", "2026-09-02 10:00:00"],
    # Invalid business value: unsupported booking status.
    ["B005", "H001", "G005", "2026-09-02", "2026-09-15", "2026-09-17", "PENDING_UNKNOWN", "2026-09-02 11:00:00"],
], columns=[
    "booking_id", "hotel_id", "guest_id", "booking_date",
    "check_in_date", "check_out_date", "status", "source_updated_at"
])

payments = pd.DataFrame([
    ["P001", "B001", 2400, "SEK", "2026-09-01 10:10:00"],
    ["P002", "B002", 0, "SEK", "2026-09-01 11:10:00"],
    ["P003", "B003", 1500, "SEK", "2026-09-01 12:10:00"],
], columns=["payment_id", "booking_id", "amount", "currency", "source_updated_at"])

hotels.to_csv(DATA_DIR / "hotels.csv", index=False)
bookings.to_csv(DATA_DIR / "bookings.csv", index=False)
payments.to_csv(DATA_DIR / "payments.csv", index=False)

print(f"Generated source files in {DATA_DIR}")
