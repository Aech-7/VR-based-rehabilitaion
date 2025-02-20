import viz
import sys
import vizact
import time
import vizshape
import vizcam

sys.path.append(r'C:\Users\Harshada\AppData\Roaming\Python\Python311\site-packages')
import serial

viz.setMultiSample(4)
viz.fov(60)
viz.go()

day = viz.addChild('sky_day.osgb')
hand_model = viz.add('hand.cfg')
hand_model.setPosition([0, 2, 0])
hand_model.setScale([3, 3, 3])
light = viz.addLight()
light.setPosition([2, 5, 5])  
light.enable()

grid = vizshape.addGrid()
grid.color(viz.GRAY)

world_axes = vizshape.addAxes()
X = viz.addText3D('X', pos=[1.1, 0, 0], color=viz.RED, scale=[0.3, 0.3, 0.3], parent=world_axes)
Y = viz.addText3D('Y', pos=[0, 1.1, 0], color=viz.GREEN, scale=[0.3, 0.3, 0.3], align=viz.ALIGN_CENTER_BASE, parent=world_axes)
Z = viz.addText3D('Z', pos=[0, 0, 1.1], color=viz.BLUE, scale=[0.3, 0.3, 0.3], align=viz.ALIGN_CENTER_BASE, parent=world_axes)

cam = vizcam.PivotNavigate(center=[0, 2, 0], distance=1)
cam.rotateRight(-30)
cam.rotateUp(15)

backgroundMusic = viz.addAudio('Music.wav')
backgroundMusic.play()
backgroundMusic.volume(0.1)

fingers = {
    "thumb": [hand_model.getBone('bone thumb 0-0'), hand_model.getBone('bone thumb 0-1')],
    "index": [hand_model.getBone('bone index 1-0'), hand_model.getBone('bone index 1-1'), hand_model.getBone('bone index 1-2')],
    "middle": [hand_model.getBone('bone middle 2-0'), hand_model.getBone('bone middle 2-1'), hand_model.getBone('bone middle 2-2')],
    "ring": [hand_model.getBone('bone ring 3-0'), hand_model.getBone('bone ring 3-1'), hand_model.getBone('bone ring 3-2')],
    "pinky": [hand_model.getBone('bone little 4-0'), hand_model.getBone('bone little 4-1'), hand_model.getBone('bone little 4-2')]
}

for joints in fingers.values():
    for joint in joints:
        joint.lock()

try:
    ser = serial.Serial('COM7', 9600, timeout=1)  
    time.sleep(1)  
except serial.SerialException:
    print("Error: Could not open serial port.")
    ser = None

def map_value(value, in_min, in_max, out_min, out_max):
    return out_min + (out_max - out_min) * (value - in_min) / (in_max - in_min)

calibration_data = {"baseline": [0] * 5, "max_bend": [0] * 5}
calibrated = False

def read_average_values(duration):
    values = []
    start_time = time.time()
    while time.time() - start_time < duration:
        if ser:
            try:
                data = ser.readline().decode().strip()
                if data:
                    flex_values = list(map(int, data.split(',')))
                    if len(flex_values) == 5:  
                        values.append(flex_values)
            except ValueError:
                continue 
    if values:
        return [sum(x) / len(x) for x in zip(*values)]
    else:
        return [0] * 5  

def calibrate():
    global calibrated
    if not ser:
        print("Error: Serial connection not established.")
        return
    
    print("Calibration step 1: Keep your hand flat with fingers extended.")
    time.sleep(5)  
    calibration_data["baseline"] = read_average_values(5)
    print(f"Baseline values recorded: {calibration_data['baseline']}")

    print("Calibration step 2: Make a fist and hold it steady.")
    time.sleep(5) 
    calibration_data["max_bend"] = read_average_values(5)
    print(f"Maximum bend values recorded: {calibration_data['max_bend']}")

    calibrated = True
    print("Calibration complete!")

def update_fingers():
    if not calibrated:
        return
    
    if ser:
        try:
            data = ser.readline().decode().strip()
            if data:
                flex_values = list(map(int, data.split(',')))
                if len(flex_values) != 5:
                    print(f"Invalid sensor data: {flex_values}")
                    return
                
                finger_angles = {
                    "thumb": [map_value(flex_values[0], calibration_data["baseline"][0], calibration_data["max_bend"][0], 0, -60)] * len(fingers["thumb"]),
                    "index": [map_value(flex_values[1], calibration_data["baseline"][1], calibration_data["max_bend"][1], 0, -60)] * len(fingers["index"]),
                    "middle": [map_value(flex_values[2], calibration_data["baseline"][2], calibration_data["max_bend"][2], 0, -60)] * len(fingers["middle"]),
                    "ring": [map_value(flex_values[3], calibration_data["baseline"][3], calibration_data["max_bend"][3], 0, -60)] * len(fingers["ring"]),
                    "pinky": [map_value(flex_values[4], calibration_data["baseline"][4], calibration_data["max_bend"][4], 0, -60)] * len(fingers["pinky"])
                }

                for finger, angles in finger_angles.items():
                    for i, joint in enumerate(fingers[finger]):
                        if i < len(angles) and i < len(fingers[finger]) - 1:  
                            if finger == "thumb":
                                joint.setEuler([0, 0, angles[i]])  
                            else:
                                joint.setEuler([angles[i], 0, 0]) 


        except (ValueError, serial.SerialException) as e:
            print(f"Error reading serial data: {e}")


calibrate()

vizact.ontimer(0.1, update_fingers)
ball = vizshape.addSphere(radius=0.4)
ball.setPosition([0, 1, 2])
ball.color(viz.RED)
ball.visible(False)

shadow = viz.addChild('shadow.wrl', alpha=0.7, cache=viz.CACHE_CLONE)
viz.link(ball, shadow, mask=viz.LINK_POS).setPos([None, 0, None])
shadow.visible(False)

air_gush_sound = viz.addAudio('Air_gush.wav')
balloon_pop_sound = viz.addAudio('Balloon pop.wav')

exercise_active = False
balloon_scale = 0.4 

def start_exercise():
    global exercise_active, balloon_scale
    exercise_active = True
    balloon_scale = 0.4
    ball.visible(True)
    shadow.visible(True)
    ball.setScale([balloon_scale, balloon_scale, balloon_scale])
    print("Balloon popping exercise started!")
    text_2D_screen = viz.addText('Pop the balloon',parent=viz.SCREEN)
    text_2D_screen.setPosition(0.3,0.9)
    text_2D_screen.color(viz.YELLOW)

    text_2D_screen.setBackdrop(viz.BACKDROP_RIGHT_BOTTOM)
    text_2D_screen.setBackdropColor([0.5,0.25,0])
    text_2D_screen.font('Times New Roman')

def update_exercise():
    global exercise_active, balloon_scale
    
    if not exercise_active or not calibrated or not ser:
        return

    try:
        data = ser.readline().decode().strip()
        if data:
            flex_values = list(map(int, data.split(',')))
            if len(flex_values) != 5:
                return

            thumb_bend = map_value(flex_values[0], calibration_data["baseline"][0], calibration_data["max_bend"][0], 0, -80)
            if thumb_bend <= -70:  
                balloon_pop_sound.play()
                ball.visible(False)
                shadow.visible(False)
                exercise_active = False
                print("Balloon popped!")
                return

            for i, finger in enumerate(["index", "middle", "ring", "pinky"], start=1):
                bend = map_value(flex_values[i], calibration_data["baseline"][i], calibration_data["max_bend"][i], 0, -80)
                if bend <= -70:
                    if balloon_scale < 1.2: 
                        balloon_scale += 0.1
                        ball.setScale([balloon_scale, balloon_scale, balloon_scale])
                        air_gush_sound.play()
                        print(f"Balloon size increased to {balloon_scale:.2f}")
                    break
    except (ValueError, serial.SerialException) as e:
        print(f"Error reading exercise data: {e}")

vizact.onkeydown('1', start_exercise)
vizact.ontimer(0.1, update_exercise)