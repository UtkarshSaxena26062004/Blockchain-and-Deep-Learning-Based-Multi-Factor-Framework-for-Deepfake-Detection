📌 Blockchain and Deep Learning-Based Multi-Factor Framework for Real-Time Deepfake Detection
🆔 Group Details
Group Number: P15
Group Leader: Utkarsh Saxena (CSE)
👥 Team Members
Utkarsh Saxena (CSE)
Tanishka Ruhela (CSE)
Ujjwal Mishra (CSE)
Manisha Kashyap (CSE)

📖 Abstract

With the rapid rise of deepfake technologies, the authenticity of digital media is under serious threat. Fake videos and manipulated content are increasingly used for misinformation, political manipulation, identity theft, and cybercrimes.

Traditional detection techniques often fail against highly realistic deepfakes. To address this, our project proposes a multi-factor, real-time deepfake detection framework that combines:

🧠 Deep Learning (CNN Models) for detecting manipulated content
🔗 Blockchain Technology for secure and tamper-proof verification
🌐 Web-Based Platform for user interaction and real-time analysis

This integrated approach ensures robust, transparent, and scalable detection, making it suitable for applications like social media moderation, journalism verification, and digital forensics.

🚀 Features
Deepfake Detection using CNN models (XceptionNet / EfficientNet)
Blockchain-based content verification
Multi-factor decision system for higher accuracy
Real-time prediction via web interface
Tamper-proof authenticity validation

🛠️ Tech Stack
Frontend: HTML, CSS, JavaScript
Backend: Flask (Python)
Deep Learning: TensorFlow / Keras
Blockchain: Ethereum (Ganache), Web3.py
Libraries: OpenCV, NumPy, Pandas

⚙️ Methodology
1️⃣ Data Preparation & Model Training
Use datasets like:
FaceForensics++
DFDC
Train CNN-based models:
XceptionNet
EfficientNet
2️⃣ Blockchain Verification Layer
Generate SHA-256 hash of videos/images
Store hash on blockchain (Ethereum)
Use smart contracts for validation
3️⃣ Multi-Factor Decision Module
Combine:
AI prediction score
Blockchain verification
Metadata analysis
Generate final authenticity score
4️⃣ Web Platform
Developed using Flask
Users can:
Upload media
Get real/fake prediction
View blockchain verification

📂 Project Structure
P15_DeepfakeDetection_FinalYearProject/
│
├── app/                        # Main Flask Application
│   ├── app.py
│   │
│   ├── blockchain/             # Blockchain related code
│   │   ├── deploy_contract.py
│   │   ├── contract_abi.json
│   │
│   ├── templates/              # HTML Templates
│   ├── static/                 # CSS, JS, Images
│   │   ├── heatmaps/
│   │   └── reports/
│   │
│   ├── uploads/                # Uploaded files (user input)
│   ├── reports/                # Generated reports
│   │
│   ├── utils/                  # Helper functions
│   │
│   └── fonts/                  # (Optional) fonts folder
│
├── model/                      # Trained models
│   └── deepfake_model.h5
│
├── data/                       # Dataset (for training/testing)
│   ├── train/
│   │   ├── fake/
│   │   └── real/
│   │
│   └── test/
│       ├── fake/
│       └── real/
│
├── datasets/                   # (Optional) raw datasets like SDFVD
│   └── SDFVD/
│       ├── videos_fake/
│       ├── videos_real/
│
├── training.py                 # Model training script
├── requirements.txt            # Dependencies
├── README.md                   # Documentation
├── .gitignore

⚙️ Installation & Setup
1. Create Virtual Environment
python -m venv venv
2. Activate Environment
Windows:
venv\Scripts\activate
Linux/Mac:
source venv/bin/activate
3. Install Dependencies
pip install -r requirements.txt
🧠 Model Training (Optional)
python training.py

⚠️ For better accuracy, use large datasets like FaceForensics++ or DFDC.

🔗 Blockchain Setup 
Start Ganache at:
http://127.0.0.1:7545
Deploy Smart Contract:
python app/blockchain/deploy_contract.py
▶️ Run the Application
python app/app.py

Open:

http://127.0.0.1:5000

🧪 Working Flow
User uploads video/image
Model predicts real or fake
Hash generated and verified via blockchain
Multi-factor system calculates final result
Result displayed to user

🎯 Applications
Social media content moderation
News and journalism verification
Digital forensics
Cybercrime prevention

⚠️ Notes
Pretrained model included for demo
Retraining recommended for higher accuracy
Blockchain module optional for demo

🔮 Future Scope
Live video streaming detection
Mobile app integration
Advanced AI models (GAN detection)
Cloud deployment

📜 License

For academic and educational use only.