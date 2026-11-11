# Install Top Gun HD

Use **standalone MesenCE 2.2.1**, the tested emulator for these packs. [Download MesenCE](https://github.com/nesdev-org/MesenCE/releases/tag/2.2.1). These packs use modern Mesen 2 / MesenCE HD-pack features; original Mesen 0.9.x and RetroArch’s **legacy Mesen core** are not compatible. That core supports pack format 106, while these projects use newer features. A separate MesenCE-based RetroArch core now exists, but these releases have not been validated with it. Standalone MesenCE is the supported setup described here.

## Install

1. Download **Top_Gun_HD_v1.0.0.zip** from the game’s Releases page. Leave the ZIP compressed.
2. Open your own supported **ROM in MesenCE**.
3. Choose **Tools > HD Packs (NES) > Install HD Pack** and select the downloaded ZIP.
4. When MesenCE reports that installation succeeded, click **OK** to reset the game and load the HD pack.

No manual extraction or folder renaming is needed for this normal installation. To update a pack, open the same ROM and install the newer release ZIP through the same menu.

## Troubleshooting

### Original graphics still appear

- Open **Settings > NES > General**, turn on **Enable HD packs**, and apply the change.
- Close and reopen the ROM after changing settings or pack files. After installation, choose **OK** when asked to reset the game and load the pack.
- Use the game’s **release HD-pack ZIP**, not GitHub’s automatic source-code ZIP or a screenshots ZIP. Keep the downloaded ZIP intact for the installer. If your browser automatically extracts downloads, download it again with automatic extraction disabled.
- Confirm that you opened the supported ROM for that pack. Different regions, revisions, translations, patches and file headers can produce different SHA-1 hashes.

### Check the active HD pack folder

In MesenCE, open **Settings > Preferences > Files** and check **Data storage location**. The `HdPacks` folder inside that location is authoritative; portable installations, redirected Documents folders and migrated Mesen2 setups can use another path.

| System | Default MesenCE HD pack folder |
| --- | --- |
| Windows | `%USERPROFILE%\Documents\MesenCE\HdPacks\` |
| macOS | `~/Library/Application Support/MesenCE/HdPacks/` |

On Windows, paste the path into File Explorer’s address bar. On Mac, use Finder **Go > Go to Folder…** (Shift–Command–G). Older or migrated setups may instead use `Documents\Mesen2\HdPacks` on Windows, `~/Library/Application Support/Mesen2/HdPacks/` on Mac, or an older `~/.config/Mesen2/HdPacks/` location. Use the location shown in Preferences rather than creating folders in all of these places.

The folder inside `HdPacks` must match the ROM’s filename **exactly, without `.nes`**, including spaces, punctuation and capitalization. For example:

| ROM filename | Required pack file |
| --- | --- |
| `Bad Dudes (NES).nes` | `HdPacks/Bad Dudes (NES)/hires.txt` |

This is a naming example, not a different supported ROM version. Renaming a ROM does not change its contents or hash. The installer normally handles the folder name for the ROM you have open. If you rename the ROM later, reinstall the pack with that ROM open or rename its pack folder to match.

Make sure `hires.txt` is directly inside the ROM-named folder, alongside all the pack assets, with no extra nested pack folder. Keep the asset filenames unchanged. If an installation is incomplete, download the release ZIP again and reinstall it through the menu.

### Check the ROM’s SHA-1

Hash the **extracted `.nes` file itself**, not the ROM ZIP or the HD-pack ZIP. Compare all 40 characters against the tested hash below; uppercase versus lowercase does not matter. A different hash means the file is not the exact tested ROM, even when its title or filename looks right. Compatibility with other dumps is not guaranteed. Do not try to fix a mismatch by renaming the file.

**Tested full-file SHA-1:** `A39376136CCCA0025063F3356B9EB41666AFF0BE`


Windows PowerShell (replace the example path with your ROM):

```powershell
Get-FileHash -Algorithm SHA1 -LiteralPath "C:\path\to\Top_Gun_HD.nes"
```

macOS Terminal:

```bash
shasum -a 1 "/path/to/Top_Gun_HD.nes"
```

### Still having trouble?

Report the pack version, emulator version, operating system, ROM SHA-1 and a screenshot in this project’s GitHub Issues. Do not upload your ROM.
