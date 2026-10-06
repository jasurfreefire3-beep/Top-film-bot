# 🎬 Professional Telegram Kino Bot (@topfilmlar_robot)

Python va zamonaviy **aiogram 3** freymvorki asosida yaratilgan professional Telegram kino boti.

---

## 🌟 Imkoniyatlari

### 👑 Admin paneli (`/admin`):
- **🎬 Kino qo'shish**:
  - Kinoni (video yoki fayl) to'g'ridan-to'g'ri yuborish yoki boshqa kanallardan **forward** qilish;
  - Kino nomini kiritish;
  - Avtomatik navbatdagi kodni qabul qilish yoki o'zingiz istagan noyob raqamli kodni belgilash;
  - Har qanday bosqichda amallarni bekor qilish (`❌ Bekor qilish`).
- **📺 Seriallar boshqaruvi**:
  - **➕ Yangi serial yaratish**: Serial nomini kiritish, avtomatik yoki qo'lda kod belgilash;
  - **🎬 Qism qo'shish**: Serial kodi va qism raqamini kiritib, video yoki fayl yuklash;
  - **🗑 Qism o'chirish**: Muayyan serialdan aniq qismni o'chirish;
  - **📑 Seriallar ro'yxati**: Barcha mavjud seriallar va ulardagi qismlar sonini ko'rish;
  - **❌ Serialni o'chirish**: Serial va uning barcha qismlarini bazadan to'liq o'chirish.
- **📊 Statistika**:
  - Bot foydalanuvchilari umumiy soni;
  - Bazadagi barcha kinolar va seriallar soni.
- **📑 Oxirgi kinolar**:
  - Eng so'nggi qo'shilgan 10 ta kinoning kodi, nomi va ko'rishlar soni.
- **🗑 Kinoni o'chirish**:
  - Kod bo'yicha bazadan kinoni o'chirish.
- **📢 Majburiy obuna (Kanallar boshqaruvi)**:
  - Homiy kanallarni qo'shish (kanal username, ID yoki post forward qilish orqali);
  - Kanallarni ko'rish va o'chirish;
  - Foydalanuvchilar kinoni yuklab olishdan avval ushbu kanallarga a'zo bo'lishga majburlanadi;
  - «✅ Obunani tekshirish» tugmasi orqali tekshirish.
- **✉️ Xabar tarqatish (Broadcast) va Tugmalar konstruktori**:
  - Barcha bot foydalanuvchilariga rasm, video, matn yoki audio xabarlar tarqatish;
  - Qadamma-qadam tugma yaratish:
    1. **Tugma rangini tanlash**: 🔴 Qizil, 🔵 Ko'k, 🟢 Yashil, ⚪️ Klassik, 🟡 Sariq, 🟣 Binafsha;
    2. **Tugma matnini kiritish**;
    3. **Tugma havolasini kiritish**;
  - Bir nechta tugmalar qo'shish va tozalash imkoniyati;
  - Yuborishdan oldin **Preview (Ko'rinish)** orqali tekshirish va tasdiqlash;
  - Yetkazilgan va yetib bormaganlar bo'yicha to'liq hisobot.

---

### 👤 Foydalanuvchilar uchun:
- **📺 Seriallar va qismlarni tomosha qilish**:
  - Serial kodini yuborganda (`1`, `2`...) barcha qismlar menyusi (`🎬 1-qism`, `🎬 2-qism`...) chiqadi;
  - Har bir qism ostida «⬅️ Barcha qismlar», «↗️ Qismni ulashish», «🎬 Ko'proq filmlar» va «💾 Saqlab qo'yish» tugmalari mavjud;
  - Nom bo'yicha qidirganda ham kinolar, ham seriallar qidiriladi.
- **🎬 Start menyusi**:
  - `/start` bosilganda **[TOP FILM](https://t.me/topfilmlar_robot)** giperhavolasi va xabar tagida to'g'ridan-to'g'ri kanalga o'tuvchi **«🎬 Barcha Filmlar»** (https://t.me/TopFilmlarUZB1) tugmasi chiqadi;
- **🔢 Kod orqali kinoni olish**:
  - Foydalanuvchi kino kodini (masalan: `1`, `15`) yuborsa, bot darhol kinoni barcha ma'lumotlari bilan chiqarib beradi.
- **🔗 Deep-link havolalar va Auto havola**:
  - Har bir kino yoki serial qo'shilganda bot darhol auto havolani (`https://t.me/topfilmlar_robot?start=KOD` yoki `start=series_KOD`) va kanal uchun tayyor post shablonini beradi.
- **🎬 Kino tagidagi interaktiv tugmalar**:
  - **↗️ Filmni ulashish** — do'stlarga yoki guruhlarga ulashish;
  - **🎬 Ko'proq filmlar** — to'g'ridan-to'g'ri https://t.me/TopFilmlarUZB1 kanaliga yo'naltiradi;
  - **💾 Saqlab qo'yish** — filmni yoki serialni foydalanuvchining shaxsiy to'plamiga saqlaydi.
- **⭐️ Saqlangan filmlar va seriallar (`/saved`)**:
  - Foydalanuvchi o'zi saqlab qo'ygan barcha filmlar va seriallar ro'yxatini ko'rishi, ularni bir bosish bilan ochishi yoki o'chirishi mumkin.
- **🔍 Qidiruv**:
  - Kino yoki serial nomi orqali qidirish (masalan: `Qasoskorlar`, `Kurtlar`). Bir nechta natija chiqsa, qulay tugmalar orqali tanlash imkoniyati.
- **👁 Ko'rishlar va yuklanishlar hisoblagichi**:
  - Kino yoki serial yuborilganda uning nomi ostida necha marta yuklangani aniq ko'rsatiladi.
- **🖼 Avto Video Cover (Muqova)**:
  - Har bir film va serial qismi yuborilayotganda `cover.jpeg` rasmi avtomatik tarzda video ustiga professional muqova (thumbnail/cover) sifatida biriktiriladi.

---

## 📁 Loyiha tuzilmasi

```text
Kino bot/
├── .env                  # Maxfiy ma'lumotlar (Bot token, admin ID)
├── config.py             # Sozlamalarni o'qish
├── database.py           # aiosqlite asinxron ma'lumotlar bazasi
├── states.py             # FSM holatlari (kino qo'shish, o'chirish, broadcast)
├── main.py               # Botni ishga tushiruvchi asosiy fayl
├── requirements.txt      # Kutubxonalar ro'yxati
├── run.sh                # Qulay ishga tushirish skripti
├── keyboards/
│   ├── admin_kb.py       # Admin paneli tugmalari
│   └── user_kb.py        # Foydalanuvchi tugmalari
└── handlers/
    ├── admin.py          # Admin buyruqlari va jarayonlari
    └── user.py           # Foydalanuvchi buyruqlari va qidiruv
```

---

## 🚀 Ishga tushirish

1. **Terminalda loyiha papkasiga o'ting:**
   ```bash
   cd "/home/kali/Documents/Kino bot"
   ```

2. **Botni ishga tushirish:**
   ```bash
   ./run.sh
   # yoki to'g'ridan-to'g'ri:
   ./venv/bin/python3 main.py
   ```

---

## ☁️ Northflank serverida ishga tushirish (Deploy)

Bot **Northflank** platformasida 24/7 rejimida ishlash uchun to'liq moslashtirilgan (Dockerfile va sozlamalar tayyor):

1. **Northflank** (https://northflank.com) hisobingizga kiring.
2. Yangi loyiha (Project) oching yoki mavjudiga kiring.
3. **Create Service** -> **Deployment Service** ni tanlang:
   - **Service Name:** `top-film-bot`
   - **Repository:** `https://github.com/jasurfreefire3-beep/Top-film-bot` (GitHub ulanadi)
   - **Branch:** `main`
   - **Build Type:** **Dockerfile** (loyiha ichidagi Dockerfile avtomatik aniqlanadi)
4. **Networking:**
   - Bot Telegram Polling rejimida ishlaganligi sababli public port ochish shart emas.
5. **Environment Variables (Ixtiyoriy, agar .env dagi qiymatlarni o'zgartirmoqchi bo'lsangiz):**
   - `BOT_TOKEN`: `8759256550:AAEyaqxm-XWtLNjLObqmMetTOlKBRMhDcT0`
   - `ADMIN_ID`: `8991315532`
   - `BOT_USERNAME`: `topfilmlar_robot`
6. **Deploy:**
   - **Create Service** tugmasini bosing. Northflank Docker image quradi va botingizni 24/7 serverda avtomatik ishga tushiradi!


