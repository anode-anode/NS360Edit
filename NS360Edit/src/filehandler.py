#filehandler.py
"""Read and edit an NFS Most Wanted (2005) Xbox 360 save.

Layout (all big-endian):
  0x4034   u32  car number of the currently selected career car
  0x4038   u8   blacklist rank (candidate)      0x4039  u32  player money
  0x5BCD   car identity table, 0x14-byte records
  0xE2F5   per-car pursuit/rap-sheet table, 0x38-byte records, record index == career_slot
             +0x00 u8  career slot (0xFF = car sold/vacated)   +0x01..03  AA 0N 0x
             +0x0C f32 heat   +0x10 u32 bounty   +0x14 u16 escaped   +0x16 u16 busted

Checksums, in the order they must be computed:
  1. MD5 @0x34..0x43 of 0x44..0x4034      2. MD5 @last 16 of 0x34..(end-16)
  3. CRC @0x10 of 0x1C..0x24              4. CRC @0x14 of 0x24..end
  5. CRC @0x18 of 0x00..0x18  (covers 3 and 4, so it goes last)
"""
import hashlib
import struct

ACTIVE_CAR_OFFSET = 0x4034
RANK_OFFSET = 0x4038            # u8, blacklist rank (candidate, not fully confirmed)
MONEY_OFFSET = 0x4039           # u32 BE player cash
MAX_MONEY = 2**31 - 1           # stay within a signed 32-bit int to be safe
IDENT_TABLE_START = 0x5BCD
IDENT_RECORD_SIZE = 0x14
IDENT_COUNT = 200

CAR_TABLE_START = 0xE2F5        # per-car rap sheet table
CAR_RECORD_SIZE = 0x38
CAR_TABLE_MAX = 64              # safety cap when scanning
MAX_BOUNTY = 2**32 - 1

HEADER_HASH_AT = 0x34
HEADER_HASH_RANGE = (0x44, 0x4034)


# ---- EA CRC32 ---------------------------------------------------------------
def _make_crc_table():
    table = []
    for i in range(256):
        crc = i << 24
        for _ in range(8):
            crc = ((crc << 1) ^ 0x04C11DB7) & 0xFFFFFFFF if crc & 0x80000000 else (crc << 1) & 0xFFFFFFFF
        table.append(crc)
    return table

_CRC_TABLE = _make_crc_table()

def ea_crc32(data):
    if len(data) < 4:
        return 0
    crc = int.from_bytes(data[:4], "big") ^ 0xFFFFFFFF
    for b in data[4:]:
        crc = (((crc << 8) | b) & 0xFFFFFFFF) ^ _CRC_TABLE[(crc >> 24) & 0xFF]
    return crc ^ 0xFFFFFFFF

class SaveError(Exception):
    """Raised with a message that is safe to show to the user."""

class MWSave:
    def __init__(self, path):
        with open(path, "rb") as f:
            self.data = bytearray(f.read())
        self.path = path
        if self.data[:4] != b"MC02":
            raise SaveError("Not MC02 save file.")

    # ---- per-car rap sheet records -----------------------------------------
    def _record_pos(self, slot):
        return CAR_TABLE_START + slot * CAR_RECORD_SIZE

    def _record_valid(self, slot):
        o = self._record_pos(slot)
        r = self.data[o:o + CAR_RECORD_SIZE]
        return len(r) == CAR_RECORD_SIZE and r[1] == 0xAA and r[2] in (3, 4, 5) and r[8:12] == b"\x00\x00\xAA\xAA"

    def _live_record_pos(self, slot):
        """Position of the record for a car that is really in the garage."""
        if not 0 <= slot < CAR_TABLE_MAX or not self._record_valid(slot):
            raise SaveError(f"No rap sheet record for career slot {slot}.")
        o = self._record_pos(slot)
        if self.data[o] != slot:
            raise SaveError(f"Career slot {slot} has no live rap sheet (car sold or lost).")
        return o

    def get_bounty(self, entry):
        o = self._live_record_pos(entry)
        return struct.unpack(">I", self.data[o + 0x10:o + 0x14])[0]

    def set_bounty(self, new_value, entry):
        try:
            value = int(str(new_value).replace(",", "").strip())
        except ValueError:
            raise SaveError("Bounty must be a whole number.")
        if not 0 <= value <= MAX_BOUNTY:
            raise SaveError(f"Bounty must be between 0 and {MAX_BOUNTY:,}.")
        o = self._live_record_pos(entry)
        self.data[o + 0x10:o + 0x14] = struct.pack(">I", value)

    # ---- player money -----------------------------------------------------
    def get_money(self):
        return struct.unpack(">I", self.data[MONEY_OFFSET:MONEY_OFFSET + 4])[0]

    def set_money(self, new_value):
        try:
            value = int(str(new_value).replace(",", "").replace("$", "").strip())
        except ValueError:
            raise SaveError("Money must be a whole number.")
        if not 0 <= value <= MAX_MONEY:
            raise SaveError(f"Money must be between 0 and {MAX_MONEY:,}.")
        self.data[MONEY_OFFSET:MONEY_OFFSET + 4] = struct.pack(">I", value)

    # ---- cars -------------------------------------------------------------
    def active_car_number(self):
        return struct.unpack(">I", self.data[ACTIVE_CAR_OFFSET:ACTIVE_CAR_OFFSET + 4])[0]

    def get_cars(self, include_historical=False):
        """Career cars joined to their rap sheet (record index == career_slot).
        Only cars currently in the garage by default (car number != 0xFFFFFFFF).
        Each item: career_slot, car_index, car_number, signature, flags, bounty,
                   heat, escaped, busted, active, in_garage."""
        active = self.active_car_number()
        cars = []
        for i in range(IDENT_COUNT):
            o = IDENT_TABLE_START + i * IDENT_RECORD_SIZE
            rec = self.data[o:o + IDENT_RECORD_SIZE]
            slot = rec[0x11]
            number = struct.unpack(">I", rec[:4])[0]
            if slot == 0xFF or rec[4:12] == bytes(8):
                continue                                   # not a career car
            in_garage = number != 0xFFFFFFFF
            if not in_garage and not include_historical:
                continue
            if not self._record_valid(slot):
                continue                                   # no rap sheet for this slot
            r = self._record_pos(slot)
            cars.append({
                "career_slot": slot,
                "car_index": i,
                "car_number": number,
                "signature": rec[4:12].hex(),
                "flags": struct.unpack(">HH", rec[0x0C:0x10]),
                "bounty": struct.unpack(">I", self.data[r + 0x10:r + 0x14])[0],
                "heat": struct.unpack(">f", self.data[r + 0x0C:r + 0x10])[0],
                "escaped": struct.unpack(">H", self.data[r + 0x14:r + 0x16])[0],
                "busted": struct.unpack(">H", self.data[r + 0x16:r + 0x18])[0],
                "active": number == active,
                "in_garage": in_garage,
            })
        return cars

    # ---- checksums ----------------------------------------------------------
    def _expected(self):
        d = self.data
        s, e = HEADER_HASH_RANGE
        return {
            "md5_header": hashlib.md5(d[s:e]).digest(),
            "md5_tail": hashlib.md5(d[0x34:-16]).digest(),
            "crc_10": ea_crc32(d[0x1C:0x24]),
            "crc_14": ea_crc32(d[0x24:]),
            "crc_18": ea_crc32(d[0x00:0x18]),
        }

    def hashes_ok(self):
        d, x = self.data, self._expected()
        return (d[0x34:0x44] == x["md5_header"] and d[-16:] == x["md5_tail"]
                and struct.unpack(">3I", d[0x10:0x1C]) == (x["crc_10"], x["crc_14"], x["crc_18"]))

    def _update_checksums(self):
        d = self.data
        s, e = HEADER_HASH_RANGE
        d[0x34:0x44] = hashlib.md5(d[s:e]).digest()
        d[-16:] = hashlib.md5(d[0x34:-16]).digest()
        d[0x10:0x14] = struct.pack(">I", ea_crc32(d[0x1C:0x24]))
        d[0x14:0x18] = struct.pack(">I", ea_crc32(d[0x24:]))
        d[0x18:0x1C] = struct.pack(">I", ea_crc32(d[0x00:0x18]))

    def save(self, out_path):
        if out_path == self.path:
            raise SaveError("Choose a different file name so your original isn't overwritten.")
        self._update_checksums()
        with open(out_path, "wb") as f:
            f.write(self.data)