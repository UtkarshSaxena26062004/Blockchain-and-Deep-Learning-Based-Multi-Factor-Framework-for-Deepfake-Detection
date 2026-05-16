# 🚀 Blockchain and Deep Learning-Based Multi-Factor Framework for Real-Time Deepfake Detection

A Final Year B.Tech Project that combines **Deep Learning** and **Blockchain Technology** for **real-time deepfake detection** and **tamper-proof media verification**.

---

## 🆔 Group Details

**Group Number:** P15  
**Supervisor:** Dr. Pradeep Kumar *(Assistant Professor, MIT)*  
**Group Leader:** Utkarsh Saxena *(CSE)*

### 👥 Team Members

| Name | Department |
|-------|------------|
| Utkarsh Saxena | CSE |
| Tanishka Ruhela | CSE |
| Ujjwal Mishra | CSE |
| Manisha Kashyap | CSE |

---

## 📖 Abstract

With the rapid rise of deepfake technologies, the authenticity of digital media is under serious threat. Fake videos and manipulated content are increasingly used for misinformation, political manipulation, identity theft, and cybercrimes.

Traditional detection techniques often fail against highly realistic deepfakes. To address this challenge, this project proposes a **multi-factor, real-time deepfake detection framework** that combines:

- 🧠 **Deep Learning (CNN Models)** for manipulated content detection  
- 🔗 **Blockchain Technology** for secure and tamper-proof verification  
- 🌐 **Web-Based Platform** for user interaction and real-time analysis  

This integrated approach ensures **robust, transparent, and scalable detection**, making it suitable for applications such as **social media moderation, journalism verification, and digital forensics**.

---

## 🚀 Features

✅ Deepfake Detection using CNN models *(XceptionNet / EfficientNet)*  
✅ Blockchain-based content verification  
✅ Multi-factor decision system for higher accuracy  
✅ Real-time prediction via web interface  
✅ Tamper-proof authenticity validation  

---

## 🛠️ Tech Stack

| Technology | Tools Used |
|------------|-------------|
| Frontend | HTML, CSS, JavaScript |
| Backend | Flask (Python) |
| Deep Learning | TensorFlow / Keras |
| Blockchain | Ethereum (Ganache), Web3.py |
| Libraries | OpenCV, NumPy, Pandas |

---

## ⚙️ Methodology

### 1️⃣ Data Preparation & Model Training
Datasets Used:
- FaceForensics++
- DFDC

CNN Models:
- XceptionNet
- EfficientNet

### 2️⃣ Blockchain Verification Layer
- Generate **SHA-256 hash** of videos/images  
- Store hash on **Ethereum blockchain**  
- Use **smart contracts** for validation  

### 3️⃣ Multi-Factor Decision Module
Combine:
- AI prediction score  
- Blockchain verification  
- Metadata analysis  

Generate final authenticity score.

### 4️⃣ Web Platform
Developed using **Flask**.

Users can:
- Upload media  
- Get real/fake prediction  
- View blockchain verification  

---

## 📂 Project Structure

```txt
P15_DeepfakeDetection_FinalYearProject/
│── app/
│── notebooks/
│── reports/
│── screenshots/
│── training.py
│── requirements.txt
│── README.md
│── .gitignore
