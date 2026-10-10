# Dailymotion – Unofficial

**Version:** 1.0.1

**Addon-ID:** `plugin.video.dailymotion_unofficial`

## Deutsch

Inoffizieller Fork des Dailymotion-Addons von gujal, der unabhängig weitergepflegt wird. Dieses Addon ist kein offizielles Angebot von Dailymotion oder Team Kodi.

### Installation

1. Lade die Installationsdatei `plugin.video.dailymotion_unofficial-1.0.1.zip` herunter, sobald sie unter [GitHub Releases](https://github.com/marbra00/Dailymotion-Unofficial/releases) veröffentlicht ist. Die GitHub-Funktion „Download ZIP“ liefert das gesamte Quellcode-Repository und nicht das installierbare Addon.
2. Öffne in Kodi **Add-ons → Paket-Symbol → Aus ZIP-Datei installieren** und wähle die Datei aus. Falls Kodi die Installation blockiert, kann sie unter **Einstellungen → System → Add-ons → Unbekannte Quellen** freigegeben werden.
3. Starte **Dailymotion – Unofficial** unter den Video-Addons.

Benötigte Module: `script.module.six` und `script.module.kodi-six`. Sie stammen aus dem offiziellen Kodi-Repository. Menübezeichnungen können je nach Sprache und Skin abweichen. Weitere Informationen: [Kodi: Add-on-Verwaltung](https://kodi.wiki/view/Add-on_manager).

### Einstellungen und Videoqualität

Der Fork hat eigene Einstellungen, Favoriten und einen eigenen Verlauf. Daten des ursprünglichen Addons werden nicht automatisch übernommen.

Der Standard ist **UHD**: Das Addon wählt die höchste verfügbare Qualität bis zu 2160p. Du kannst die maximale Auflösung in den Addon-Einstellungen begrenzen, zum Beispiel auf **FHD (1080p)** oder **SD (480p)**. Eine höhere Qualität kann mehr Daten verbrauchen. UHD erzeugt keine höhere Auflösung, wenn Dailymotion das Video nur in geringerer Qualität anbietet.

Updates werden durch Installation einer neueren Addon-ZIP eingespielt.

### Einbindung über .strm-Dateien

Ersetze `VIDEOID` durch die Dailymotion-Video-ID. Eine `.strm`-Datei enthält eine der folgenden Zeilen:

Video:

```text
plugin://plugin.video.dailymotion_unofficial/?url=VIDEOID&mode=playVideo
```

Livestream:

```text
plugin://plugin.video.dailymotion_unofficial/?url=VIDEOID&mode=playLiveVideo
```

Bestehende Links mit `plugin.video.dailymotion_com` starten weiterhin das Originaladdon. Die Livestream-Funktion wurde übernommen; sie wurde bei der Wiedergabereparatur nicht separat getestet.

### Herkunft und Lizenz

Originalprojekt: [Gujal00/Kodi-Official](https://github.com/Gujal00/Kodi-Official), bisherige Addon-ID `plugin.video.dailymotion_com`. Die Git-Historie enthält die ursprünglichen Beiträge. Fork-Maintainer: **marbra00**. Die Wiedergabereparatur und die Vorbereitung des Forks entstanden mit KI-Unterstützung.

Lizenz: **GPL-3.0-or-later**. Der vollständige GPLv3-Lizenztext liegt in [LICENSE](LICENSE). Die bestehenden Lizenz- und Autorenhinweise bleiben erhalten. Quellcode des Forks: [marbra00/Dailymotion-Unofficial](https://github.com/marbra00/Dailymotion-Unofficial).

## English

An unofficial fork of gujal's Dailymotion addon, maintained independently. This addon is not an official product of Dailymotion or Team Kodi.

### Installation

1. Download `plugin.video.dailymotion_unofficial-1.0.1.zip` once it is published on [GitHub Releases](https://github.com/marbra00/Dailymotion-Unofficial/releases). GitHub's “Download ZIP” provides the complete source repository rather than an installable addon package.
2. In Kodi, open **Add-ons → package icon → Install from ZIP file** and select the file. If installation is blocked, it can be enabled under **Settings → System → Add-ons → Unknown sources**.
3. Open **Dailymotion – Unofficial** from the video addons.

Required modules: `script.module.six` and `script.module.kodi-six`, available from the official Kodi repository. Menu labels may vary by language and skin. See [Kodi: Add-on manager](https://kodi.wiki/view/Add-on_manager).

### Settings and video quality

This fork has separate settings, favourites and history. Data from the original addon is not migrated automatically.

The default is **UHD**: the addon selects the highest available quality up to 2160p. You can limit the maximum resolution in the addon settings, for example to **FHD (1080p)** or **SD (480p)**. Higher quality may use more data. UHD does not increase the resolution of videos only offered at a lower quality by Dailymotion.

Updates require installing a newer addon ZIP.

### .strm files

Replace `VIDEOID` with the Dailymotion video ID. A `.strm` file contains one of these lines:

Video:

```text
plugin://plugin.video.dailymotion_unofficial/?url=VIDEOID&mode=playVideo
```

Livestream:

```text
plugin://plugin.video.dailymotion_unofficial/?url=VIDEOID&mode=playLiveVideo
```

Existing links using `plugin.video.dailymotion_com` still launch the original addon. Livestream support was retained but was not tested separately during the playback repair.

### Credits and licence

Original project: [Gujal00/Kodi-Official](https://github.com/Gujal00/Kodi-Official), original addon ID `plugin.video.dailymotion_com`. Git history preserves the original contributions. Fork maintainer: **marbra00**. AI assistance was used for the playback repair and fork preparation.

Licence: **GPL-3.0-or-later**. The complete GPLv3 licence text is included in [LICENSE](LICENSE). Existing licence and author notices are retained. Fork source: [marbra00/Dailymotion-Unofficial](https://github.com/marbra00/Dailymotion-Unofficial).
