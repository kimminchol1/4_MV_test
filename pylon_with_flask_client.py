import cv2
import threading
import socket
import numpy as np
from flask import Flask,Response,render_template
from pypylon_opencv_viewer import BaslerOpenCVViewer
from pypylon import pylon
app = Flask(__name__)
# disp_frame = {}
@app.route('/')
def index():
    return render_template('index.html')







# new_width = camera.Width.GetValue() - camera.Width.GetInc()
# if new_width >= camera.Width.GetMin():
#     camera.Width.SetValue(new_width)






# @app.route('/client')
# def client():
#     return Response(getFrames(), mimetype = 'multipart/x-mixed-replace; boundary=frame')

# @app.route('/webcam')
# def webcam():
#     # return render_template('index.html')
#     return Response(getFrames('webcam'), mimetype = 'multipart/x-mixed-replace; boundary=frame')

# def getFrames():
#     global disp_frame

#     while True:
#         if disp_frame is not None:
#             ret, jpeg = cv2.imencode('.jpg', disp_frame, [int(cv2.IMWRITE_JPEG_QUALITY), 90])
            
#             bframe = jpeg.tobytes()
#             if bframe is not None:
#                 yield (b'--frame\r\n'
#                         b'Content-Type: image/jpeg\r\n\r\n' + bframe + b'\r\n\r\n')
#         else :
#              yield (b'--frame\r\n'
#                     b'Content-Type: image/jpeg\r\n\r\n\r\n\r\n')

class ReadAndEncode(threading.Thread):
    def __init__(self,barsler_cam=None, sock=None):
        threading.Thread.__init__(self)
        # self.cap = None
        self.frame = None
        self.sock = sock
        
        # self.string_result = None
        if barsler_cam is not None:
            barsler_cam.Open()
            self.viewer = BaslerOpenCVViewer(barsler_cam)
            self.converter = pylon.ImageFormatConverter()
            # self.viewer.set(3,640)
            # self.viewer.set(4,480)

    def run(self):
        # th_send.start_check = True
        
        barsler_cam.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)
        while barsler_cam.IsGrabbing():
            grabResult = barsler_cam.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)
            
            if grabResult.GrabSucceeded():
                frame = self.converter.Convert(grabResult)
                img = frame.GetArray()
                self.frame = img
                # self.frame = cv2.resize(self.frame, dsize=(640,480), interpolation=cv2.INTER_AREA)
                encode_param = [int(cv2.IMWRITE_JPEG_QUALITY),80]
                data, encoded_frame = cv2.imencode('.jpg', self.frame, encode_param)
                if data:

                    string_data = np.array(encoded_frame).tostring()
                    self.sock.send(str(len(string_data)).encode().ljust(16))
                    self.sock.send(string_data)
                    # decimg=cv2.imdecode(string_data,1)
                    cv2.imshow('CLIENT',self.frame)
                    # disp_frame = self.frame
                    grabResult.Release()
                    if cv2.waitKey(1) & 0xFF == 27:
                        break
        barsler_cam.Close()
class SendEncode(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.client_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.client_socket.connect((HOST,PORT))
        self.start_check = False
        
    def run(self):
        th_enc = ReadAndEncode(barsler_cam,self.client_socket)
        th_enc.start()
        self.start_check=True
            
            # self.client_socket.send(str(len(th_enc.string_result)).ljust(24))
            # self.client_socket.send(th_enc.string_result)
            # self.client_socket.close()
if __name__ == '__main__':
    HOST = '192.168.0.121'
    PORT = 6000
    barsler_cam = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateFirstDevice())
    url = barsler_cam.Open()
    # url = 0
    # print(pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateFirstDevice()))
    th_send = SendEncode()
    th_send.start()

    # app.run(host='127.0.0.1', debug = False, port=8000)