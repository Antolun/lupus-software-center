# PiSiM - PiSi Market (Rust + Tauri Edition)

LupuS işletim sistemi için modern, hızlı ve hafif paket yöneticisi ve uygulama mağazası.

## 🚀 Özellikler

- **Rust Backend**: PiSi ve Flatpak paketlerinin yüksek performanslı, asenkron ve güvenli yönetimi.
- **Tauri UI**: PyQt6 arayüzünün renk paleti, tipografi, simgeler ve düzeniyle %100 birebir Vanilla HTML/CSS/JS arayüz.
- **PiSi & Flatpak Desteği**: Hem PiSi repolarındaki yerel paketleri hem de FlatHub uygulamalarını kurma, kaldırma ve güncelleme.
- **Canlı Arama & Kategori Filtreleme**: Hızlı paket arama ve kategorilere göre listeleme.
- **Sistem Tepsisi (Tray Icon)**: Arka planda çalışma ve güncelleme denetimi.
- **Çoklu Dil (i18n)**: Türkçe ve İngilizce desteği.
- **Koyu / Açık Tema**: Sistem teması ile tam uyumlu görünüm.

## 🛠️ Derleme ve Çalıştırma

### Geliştirme Modunda Çalıştırma:

```bash
cargo tauri dev
```

### Üretim Paketi Oluşturma:

```bash
cargo tauri build
```

## 📂 Proje Yapısı

- `src-tauri/`: Rust backend kodları, PiSi/Flatpak entegrasyonu, sistem tepsisi ve Tauri IPC komutları.
- `ui/`: Vanilla HTML5, CSS3 ve JavaScript frontend dosyaları ve grafik varlıkları.
