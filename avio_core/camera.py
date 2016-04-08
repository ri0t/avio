from avio_core.component import AVIOComponent
from avio_core.events import cameraframe

import cv2

class CVCamera(AVIOComponent):
    def __init__(self, device_id=0, targetresolution=(40, 16), *args, **kwargs):
        super(CVCamera, self).__init__(*args, **kwargs)
        self.targetresolution = targetresolution
        self.cam = cv2.VideoCapture(device_id)
        self.cam.set(3, 320)
        self.cam.set(4, 240)

        self.recording = True

    def takepicture(self):
        if self.recording:
            err, frame = self.cam.read()

            if frame == None:
                print("Oh, no camera attached! Change this and rerun!")

            newframe = cv2.resize(frame, self.targetresolution)
            self.fireEvent(cameraframe(newframe))
