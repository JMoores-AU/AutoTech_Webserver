import logging
from pathlib import Path

class IPData:
    _cache = None

    @classmethod
    def parse_ip_list(cls, file_path="IP_list_Ref.txt"):
        if cls._cache is not None:
            return cls._cache

        ip_data = {}
        current_category = "DEFAULT"

        try:
            file_path = Path(file_path)
            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")

            with file_path.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()

                    if not line:
                        continue

                    if line.startswith("######") and line.endswith("######"):
                        current_category = line.strip("# ").upper()
                        ip_data.setdefault(current_category, [])
                        continue

                    parts = line.split()
                    if len(parts) >= 2:
                        name = parts[0]
                        ip = parts[1]
                        avi = parts[2] if len(parts) > 2 else None
                        ip_data.setdefault(current_category, []).append(
                            {"name": name, "ip": ip, "avi": avi}
                        )
                    else:
                        logging.warning(f"Skipping malformed line: {line}")

            cls._cache = ip_data
            return ip_data

        except Exception as e:
            logging.error(f"Error parsing IP list: {e}")
            raise
