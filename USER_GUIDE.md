# 🌙 Jashn-e-Ghadeer Quiz App - User Guide


## 🛠️ For Admins : Creating Quizzes

### 1. **Creating a New Quiz**
- Go to **"Manage Quizzes"** from the home screen.
- Click **"Create New Quiz"**.
- Enter a name (e.g., "Ramadan Special") and choose if you want a **Timer**.

### 2. **Managing Age Groups**
Age groups allow you to tailor content for different difficulty levels.
- **Add Age Group**: Give it a name like "Juniors" or "Seniors".
- **Theme Selection**: Choose a visual theme for this group:
  - 🌙 **Crescent Moon**: Deep blue night sky with floating stars.
  - 🐪 **Desert Journey**: Animated camels and dunes.
  - 🕌 **Masjid**: Green and gold architectural theme.
  - 🌺 **Garden**: Peaceful nature visuals.
- **Celebration Type**: Pick what happens when they get an answer right (Confetti, Fireworks, or Balloons).

### 3. **Question Sets & Round Robin**
- You can create multiple **Question Sets** (Set A, Set B, etc.) for each age group.
- **Round Robin System**: The app automatically rotates through sets. If a child plays "Set A", the next child will automatically get "Set B", ensuring variety.

---

## 📊 Data Management (Excel)

You can easily backup or edit your quizzes using Excel.

### **Exporting**
- In the **Quiz Manager**, click the **"Export"** button next to any quiz.
- This downloads an `.xlsx` file with all your questions and settings.

### **Importing**
- Click **"Import form Excel"**.
- Select a valid Jashn-e-Ghadeer Excel file.
- The app will validate the file and add the quiz to your list.

### **Excel Structure Guide**
If you want to create quizzes directly in Excel:
1. **Sheet 1 ("Config")**:
   - `Quiz Name`: Name of your quiz
   - `Has Timer`: TRUE or FALSE
   - `Timer Seconds`: Number (e.g., 30)
2. **Sheet 2+ (Age Group Name)**:
   - Columns needed: `Set Name`, `Question`, `Option A`, `Option B`, `Option C`, `Option D`, `Correct`, `Theme`, `Celebration`.
   - **Correct**: Must be the letter (A, B, C, or D).

---

## 🎨 Themes & Customization

The app comes with beautiful, animated themes:

| Theme | Visuals | Best For |
|-------|---------|----------|
| **Crescent Moon** | Starry night, floating moon, nebula | Evening events, general use |
| **Desert Journey** | Golden sands, walking camels, sunset | History, Prophet stories |
| **Ocean Voyage** | Blue waves, bobbing ships, fish | Nature topics, general fun |
| **Masjid** | Green/Gold tones, minaret silhouettes | Islamic jurisprudence, Quran |
| **Lantern** | Warm amber, hanging lamps | Ramadan vibes |
| **Calligraphy** | Parchment texture, ink flourishes | Arabic, History |
