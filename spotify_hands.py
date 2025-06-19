import numpy as np
import cv2
import mediapipe as mp 
from mediapipe.tasks.python import vision
from mediapipe.framework.formats import landmark_pb2

import sp_controller
import time

printv = lambda *a, **k : None

def draw_landmarks_on_image(rgb_image, hand_landmarks_list: list):
    if hand_landmarks_list == []:
        printv("No landmarks to draw")
        return rgb_image
    else:
        annotated_image = np.copy(rgb_image)

        # Loop through the detected hands to visualize.
        for idx in range(len(hand_landmarks_list)):
            hand_landmarks = hand_landmarks_list[idx]
        
            # Draw the hand landmarks.
            hand_landmarks_proto = landmark_pb2.NormalizedLandmarkList()
            hand_landmarks_proto.landmark.extend(
                [landmark_pb2.NormalizedLandmark(x=landmark.x, y=landmark.y, z=landmark.z) for landmark in hand_landmarks]
            )
            mp.solutions.drawing_utils.draw_landmarks(
                annotated_image,
                hand_landmarks_proto,
                mp.solutions.hands.HAND_CONNECTIONS,
                mp.solutions.drawing_styles.get_default_hand_landmarks_style(),
                mp.solutions.drawing_styles.get_default_hand_connections_style()
            )
        return annotated_image
    
class recognizer_and_result():
    def create_recognizer(self):
        def update_result(result: vision.GestureRecognizerResult, output_image: mp.Image, timestamp_ms: int):
            #TODO: let user choose the delay 
            #hands take time to move. putting a delay on how fast the results can update limits intermediate movements being seen as gestures
            if(timestamp_ms > self.timestamp + 750):
                self.result = result
                self.timestamp = timestamp_ms
        
        options = vision.GestureRecognizerOptions( 
            base_options = mp.tasks.BaseOptions(model_asset_path="./gesture_recognizer.task"), # path to model
            running_mode = vision.RunningMode.LIVE_STREAM, # running on a live stream
            num_hands = 1, # track one hand
            min_hand_detection_confidence = 0.5, # lower the value to get predictions more often
            min_hand_presence_confidence = 0.5, # lower the value to get predictions more often
            min_tracking_confidence = 0.3, # lower the value to get predictions more often
            result_callback=update_result)
        
        self.gesture_recognizer = vision.GestureRecognizer.create_from_options(options)
    
    def detect_async(self, frame):
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data = frame)
        self.gesture_recognizer.recognize_async(image = mp_image, timestamp_ms = int(time.time() * 1000))

    def gesture_to_action(self):
        if(not self.result):
            return
        try:
            gesture = self.result.gestures
            name = gesture[0][0].category_name
            
            #prevent repeat calls
            if(name == self.prev_gesture):
                return
            self.prev_gesture = name
            
            self.gesture_map[name]()
        except Exception as e:
            printv("Error recognizing gesture: \n", e)
    
    def close(self):
        self.gesture_recognizer.close()

    def __init__(self, gesture_map):
        self.result = vision.GestureRecognizerResult
        self.gesture_recognizer = vision.GestureRecognizer
        self.timestamp = 0
        self.gesture_map = gesture_map
        self.create_recognizer()
        self.prev_gesture = "None"

def main():
    #TODO: just use the command line
    un = input("Enter your username, then password: ")
    pw = input()

    #TODO: use verbose printing 
    verbose = input("Would you like to run the program with debugging information? y/N: ")
    printv = print if verbose == 'y' or verbose == 'Y' else lambda *a, **k: None
    sp_controller.printv = printv

    headless = input("Would you like to run the program in headless mode? y/N: ")
    headless = True if headless == 'y' or headless == 'Y' else False

    controller = sp_controller.SPController(headless, un, pw)

    gesture_map = {
        "Unknown"       : lambda : printv("Unknown"),
        "None"          : lambda : printv("None"),
        "Closed_Fist"   : controller.pause_play,
        "Open_Palm"     : lambda : printv("Open_Palm"),
        "Pointing_Up"   : lambda : printv("Pointing_Up"),
        "Thumb_Down"    : controller.rewind,
        "Thumb_Up"      : controller.skip,
        "Victory"       : lambda : printv("Victory"),
        "ILoveYou"      : lambda : printv("ILoveYou")
    }
    
    try:
        if(not headless):
            cv2.namedWindow("preview")
        vc = cv2.VideoCapture(0)

        if vc.isOpened():
            rval, frame = vc.read()
        else: 
            print("Could not open camera")
            rval = False

        recognizer = recognizer_and_result(gesture_map)
        recognizer.detect_async(frame)

        #BUG
        #hand_landmarks field is not always present
        #I believe that the asynchronous calling of the recognizer means that the 
        #hand_landmarks field is not present at the time when it would first be accessed by the system
        #this is in spite of the fact that the result field is present on the recognizer
        #I am quite sure there is a better solution, but this works for now
        landmarks_present = False
        while(not landmarks_present):
            try:
                recognizer.result.hand_landmarks
                landmarks_present = True
            except AttributeError as e:
                printv("landmarks not present on recognizer result")
                time.sleep(.5)

        while rval:
            ret, frame = vc.read()
            if(not ret): continue
            
            frame = cv2.flip(frame, 1)
            recognizer.detect_async(frame)
            
            recognizer.gesture_to_action()
            if(not headless):
                frame = draw_landmarks_on_image(frame, recognizer.result.hand_landmarks)
                cv2.imshow("preview", frame)
            

            key = cv2.waitKey(1)
            if key == 27:
                break
            
    except Exception as e:
        printv(e, "closing out...")
        
    recognizer.close()
    vc.release()
    if(not headless):
        cv2.destroyWindow("preview")


if __name__ == "__main__":
    main()    