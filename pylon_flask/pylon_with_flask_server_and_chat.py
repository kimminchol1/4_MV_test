
import socket
import threading
import cv2
import numpy as np
from collections import deque
import time
from flask import Flask,render_template,Response
from darknet.yolo_python import net
from flask_socketio import SocketIO,emit
from flask_cors import CORS
app = Flask(__name__)
# disp_frame = {}
# get_frame = []
app.secret_key = "secret"
socketio = SocketIO(app, cors_allowed_origins='*',async_mode = "threading")
#async_mode는 engineio.server 설정 옵션으로 비동기 처리를 위한 모드옵션. 기본모드는 eventlet
CORS(app)
# data = None

@app.route('/')
def index():
    return render_template('./index.html')
    # @app.route('/client')
    # def client():
    #     # return render_template('index.html')
    #     return Response(getFrames(), mimetype = 'multipart/x-mixed-replace; boundary=frame')

@app.route('/server')
def server():
    return Response(getFrames(), mimetype = 'multipart/x-mixed-replace; boundary=frame')

@socketio.on('my event')
def handle_msg(data):
    print('Message:' + str(data))
    socketio.emit('my response', data ,callback=message_callback()) #서버에게 메시지 받았다고 응답 메세지 보냄
        
def message_callback():
    print("message was received!!")

def getFrames():
    global disp_frame

    while True:
        if disp_frame is not None:
            ret, jpeg = cv2.imencode('.jpg', disp_frame, [int(cv2.IMWRITE_JPEG_QUALITY), 90])
            if ret:
                bframe = jpeg.tobytes()
                if bframe is not None:
                    yield (b'--frame\r\n'
                            b'Content-Type: image/jpeg\r\n\r\n' + bframe + b'\r\n\r\n')
        else :
            yield (b'--frame\r\n'
                    b'Content-Type: image/jpeg\r\n\r\n\r\n\r\n')

class ReceiveVideoManager(threading.Thread):
    def __init__(self,conn=None,addr=None):
        threading.Thread.__init__(self)
        self.conn = conn
        self.addr = addr
        
        self.decoded_frame = None
        self.frame_count = 0
        self.results = []
        

    def run(self):
        while th_server.start_check:

            try:
                length = self.decode_video(16)
                stringData = self.decode_video(int(length))
                data = np.fromstring(stringData, dtype='uint8')
                self.decoded_frame = cv2.imdecode(data,cv2.IMREAD_COLOR)
                self.frame_count +=1
                
                # cv2.imshow('SERVER', self.decoded_frame)
                # cv2.waitKey(1)

                if (self.frame_count%3 == 0) & len(th_server.stream_deque) < 30:
                    th_server.stream_deque.append([self, self.decoded_frame])
                
                
            except Exception as e:
                print(e)
                th_server.start_check = False
            
            
    def decode_video(self,count):
        buf = b''
        while count:
            if count >0:
                newbuff = self.conn.recv(count)
            if not newbuff:
                return None
            buf += newbuff
            count -= len(newbuff)
        return buf


class TcpManager(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((HOST,PORT))
        self.server_socket.listen()
        
        self.stream_deque = deque()
        self.thread_list = []
        self.start_check = False

    def run(self):
        print("영상 불러오는중..")
        
        while True:
            conn, addr = self.server_socket.accept()
            self.start_check = True
            print("연결됨")
            
            self.thread_list.append(ReceiveVideoManager(conn,addr))
            self.thread_list[-1].start()
            self.detect_video()
        # Detection
            th_chat = threading.Thread(target=handle_msg,args=(None,))
            th_chat.start()
            

    def detect_video(self):
        # global get_frame
        while True:
            if len(self.stream_deque) > 0 :
                th_A, get_frame = self.stream_deque.popleft()

                results= net.detect(get_frame,0.5,0.5)
                th_A.results = results
                # cv2.imshow('server',get_frame)
                # cv2.waitKey(1)
            time.sleep(0.0001)
                
            
            

class DetectManager(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        
    def run(self):
        global disp_frame
        while True:
            for th_A in th_server.thread_list:
                if th_A.decoded_frame is not None:
                    frame = th_A.decoded_frame.copy()
                    
                    for detection in th_A.results:
                        label = detection[0]
                        confidence = detection[1]
                        x,y,w,h = detection[2]
                        xmin = int(round(x - (w / 2)))
                        xmax = int(round(x + (w / 2)))
                        ymin = int(round(y - (h / 2)))
                        ymax = int(round(y + (h / 2)))

                        labelText = label + ": " + str(np.rint(100 * confidence)) +"%"

                        cv2.rectangle(frame, (xmin, ymin), (xmax, ymax), (0,0,255), 2)
                        cv2.putText(frame, labelText, (xmin,ymin-12), cv2.FONT_HERSHEY_DUPLEX, 0.6, (0,0,255), 1)
                        
                    
                    cv2.imshow('SERVER', frame)
                    disp_frame = frame

            if cv2.waitKey(1) & 0xff == 27:
                cv2.destroyAllWindows()
                exit()

            time.sleep(1/30)


if __name__ == '__main__':
    HOST = '192.168.0.121'
    PORT = 6000
    # thread_list.append(th_read)
    # for thr in self.thread_list:
    #     thr.start()
    
    th_server = TcpManager()
    th_server.start()

    
    
    th_detect = DetectManager()
    th_detect.start()

    # app.run(host='localhost', debug = False, port=5000)
    socketio.run(app)
    