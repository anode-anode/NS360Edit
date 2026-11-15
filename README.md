# NS360Edit
A lightweight *Need for Speed: Most Wanted* (2005) (Xbox 360) save file editor, built primarily for use with macOS recompilations of the game such as [Speedbreaker](https://github.com/SpeedBreakerProject/speedbreaker).

* **Lightweight functionality:** Read, modify, and save game files.
* **Valid checksums:** Matches original EA CRC32 and MD5 checksums.

### Motivations
* Despite the game being over 20 years old and having probably a dozen existing save editors, I could not find one that formatted save files properly for the Xbox 360 version to accept. This tool correctly calculates and applies both EA CRC32 and MD5 checksums.
* **Intentionally pared back:** The primary goal is bypassing late-game bounty milestones, so functionality is stripped down compared to full-featured tools like [sprintstate's NFSMW Save Editor](https://github.com/sprintstate/nfs-mw-save-editor) (which provided the lookup tables and EA CRC32 checksum logic used in this project).
  
<div align="center">
  <img src="https://github.com/user-attachments/assets/ab424b18-8452-43a2-ba5f-59062f80c489" alt="Description" width="500">
</div>


## Platforms & Installation
Pre-built release binaries are currently available for **macOS only** on the [Releases](https://github.com/anode-anode/NS360Edit/releases) page. 

### Running from Source (Windows & Linux)
Requires **Python 3.8 – 3.11**. From the project root directory, run the following in your terminal:

1. **Create and activate a virtual environment** *(optional, recommended)*:
   * **Windows:** `python -m venv venv && venv\Scripts\activate`
   * **Linux:** `python3 -m venv venv && source venv/bin/activate`

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
3. **Run script:**
   ```bash
   python3 main.py

## License
Licensed under the GNU GPL v3.0.

