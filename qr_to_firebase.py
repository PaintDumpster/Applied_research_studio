import firebase_admin
from firebase_admin import credentials, firestore
import cv2
from pyzbar.pyzbar import decode
import time


cred = credentials.Certificate("serviceAccount.json")
firebase_admin.initialize_app(cred)
db = firestore.client()



cap = cv2.VideoCapture(0)
print("Ready to scan 2 QR codes...")

first_code = None
second_code = None

while True:
    success, frame = cap.read()
    if not success:
        continue

    codes = decode(frame)

    for code in codes:
        data = code.data.decode("utf-8")

        if not first_code:
            first_code = data
            print(f"First QR scanned: {first_code}")
            time.sleep(1)  # Small delay to avoid duplicate scans
        elif not second_code and data != first_code:
            second_code = data
            print(f"Second QR scanned: {second_code}")

            # Upload both to Firebase
            qr_data = {
                "topography": first_code,
                "streets": second_code,
                "timestamp": firestore.SERVER_TIMESTAMP
            }
            db.collection("qr_scans").document("latest").set(qr_data)
            print("Sent to Firebase!")
            first_code = None
            second_code = None
            print("\nReady for next set of QRs...\n")
            time.sleep(2)

    cv2.imshow("QR Scanner", frame)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
