# 🧩 Virtual Puzzle with Hand Gesture Controls

**Solve a Jigsaw Puzzle Using Only Your Hands**

🖐️ Hand Tracking • 🎮 Gesture Controls • 📷 Webcam-Based • 🧩 Interactive Puzzle

Virtual Puzzle with Hand Gesture Controls is a Python-based computer vision project that allows users to solve a **4×4 jigsaw puzzle** using **real-time hand gestures** detected through a webcam. Powered by **OpenCV**, **MediaPipe**, and **CVZone**, the game offers an intuitive touch-free experience where puzzle pieces are picked up and swapped using simple pinch gestures.

This project is ideal for learning **Computer Vision, Hand Tracking, Human-Computer Interaction, and Gesture-Based Gaming with Python**.

---

# ✨ Features

🖐️ **Real-Time Hand Tracking**
Detects and tracks both hands using MediaPipe and CVZone.

🤏 **Pinch Gesture Controls**
Use thumb and index finger pinches to interact with the puzzle.

🧩 **Interactive 4×4 Puzzle**
Automatically slices an image into 16 pieces and shuffles them.

📦 **Custom Puzzle Area**
Create your own puzzle box by selecting the top-left and bottom-right corners with your hands.

🔄 **Piece Swapping**
Drag puzzle pieces to swap their positions with other pieces.

✅ **Solved Piece Highlight**
Correctly placed pieces are highlighted with a green border.

🎨 **Custom Puzzle Image**
Place your own **puzzle.jpg** file in the project folder to use a custom image.

---

# 🧠 Technologies Used

* Python 🐍
* OpenCV – Computer Vision
* MediaPipe – Hand Landmark Detection
* CVZone – Simplified Hand Tracking
* NumPy – Array Processing
* Pillow – Image Handling

---

# 📂 Project Structure

```text
Virtual-puzzle-with-hand-gesture-controls
│
├── puzzle_game.py
├── requirements.txt
├── README.md
├── LICENSE
└── puzzle.jpg (Optional)
```

---

# ⚙️ Installation

## 1️⃣ Clone the Repository

```bash
git clone https://github.com/rsamwilson2323-cloud/Virtual-puzzle-with-hand-gesture-controls.git
cd Virtual-puzzle-with-hand-gesture-controls
```

---

## 2️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

Or install manually:

```bash
pip install opencv-python cvzone mediapipe numpy Pillow
```

---

# ▶️ Usage

Run the game using:

```bash
python puzzle_game.py
```

Allow access to your webcam when prompted.

If **puzzle.jpg** is not found, the game automatically generates a colorful placeholder puzzle.

---

# 🎮 How to Play

## 🛠️ Setup Phase

✋ **Left Hand Pinch**
Sets the **Top-Left Corner** of the puzzle.

🤚 **Right Hand Pinch**
Sets the **Bottom-Right Corner**.

📦 Hold both pinches together to preview the puzzle area.

✅ Release both pinches to generate the puzzle.

---

## 🧩 Play Phase

🤏 Pinch over a puzzle piece to grab it.

🖐️ Drag the piece to another grid position.

🔄 Release to swap pieces.

🟩 Correctly placed pieces are highlighted in green.

🏆 Arrange all pieces correctly to complete the puzzle.

---

# ⌨️ Controls

| Key | Action |
|------|--------|
| **ENTER** | Quit the game |
| **SPACE** | Reset the puzzle |

---

# 📸 Custom Puzzle Image

To use your own image:

1. Choose any square image.
2. Rename it as:

```text
puzzle.jpg
```

3. Place it inside the project folder.

The game will automatically slice it into a **4×4 puzzle**.

---

# 🧠 How It Works

1. Webcam captures live video.
2. MediaPipe detects hand landmarks.
3. CVZone processes hand gestures.
4. Pinch gestures are used for interaction.
5. Puzzle pieces are swapped inside the selected grid.
6. The game checks the puzzle state in real time.
7. When all pieces are correctly placed, the puzzle is completed.

---

# 🚀 Future Improvements

- 🎵 Background music
- ⏱️ Timer and Scoreboard
- 🏅 Leaderboard
- 🧩 Multiple Difficulty Levels
- 📂 Load Images from File Explorer
- 🌈 Animated Effects
- 🎮 Full-Screen Mode

---

# 🤝 Contributing

Contributions are welcome and appreciated.

Steps to contribute:

1. Fork the repository
2. Create a new feature branch
3. Commit your changes
4. Push to your branch
5. Submit a Pull Request

---

# 🙏 Acknowledgments

💡 OpenCV Community

🖐️ Google MediaPipe Team

🚀 CVZone Library

🐍 Python Community

---

# ⭐ Support

If you like this project:

⭐ Star the repository

🍴 Fork it

💬 Share your feedback

---

# 👨‍💻 Author

**Sam Wilson**

🌐 GitHub

https://github.com/rsamwilson2323-cloud

💼 LinkedIn

https://www.linkedin.com/in/sam-wilson-14b554385

---

# 📜 License

This project is licensed under the **MIT License**.
