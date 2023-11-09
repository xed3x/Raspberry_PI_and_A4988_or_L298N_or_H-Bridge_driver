import RPi.GPIO as GPIO
import time, json, sys

driver = sys.argv[1]
what = sys.argv[2]

if driver == '-' and what == 'check_pins':
  GPIO.setmode(GPIO.BCM) # GPIO-Modus auf BCM setzen
  GPIO.setup(17, GPIO.IN) # Pin 17 als Eingang konfigurieren
  GPIO.setup(27, GPIO.IN) # Pin 17 als Eingang konfigurieren
  status_pin_17 = GPIO.input(17) # Den Status des Pins lesen
  status_pin_27 = GPIO.input(27) # Den Status des Pins lesen
  GPIO.cleanup() # Pin 17 freigeben
  print(f"Status von Pin 17: {status_pin_17} und Pin 27: {status_pin_27}")
if driver == 'A4988': # for an A4988 step motor driver
  if what == '4-phase':
    inputs = { 'steps':int(sys.argv[3]), 'speed':int(sys.argv[4]) }
    var = {
       'pic':'Raspberry-Pi-A4988-4-Phase.jpg'
      ,'cmd':'python3 02_motor.py A988 4-phase 400 200'
      ,'steps':inputs['steps'],'speed':inputs['speed']
      ,'pin':{'dir':27,'step':17,'U':14},'forward':( inputs['steps'] >= 0 )
    }
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(var['pin']['dir'], GPIO.OUT);  GPIO.setup(var['pin']['step'], GPIO.OUT);  GPIO.setup(var['pin']['U'], GPIO.OUT)
    GPIO.output(var['pin']['dir'], GPIO.LOW); GPIO.output(var['pin']['step'], GPIO.LOW); GPIO.output(var['pin']['U'], GPIO.HIGH)
    GPIO.output(var['pin']['dir'], GPIO.HIGH if var['forward'] else GPIO.LOW)
    time_per_step = 1.0 / var['speed']
    for count in range(abs( var['steps'] )):
      GPIO.output(var['pin']['step'], GPIO.HIGH)
      GPIO.output(var['pin']['step'], GPIO.LOW)
      time.sleep(time_per_step)
    GPIO.output(var['pin']['U'], GPIO.LOW)
    GPIO.output(var['pin']['dir'], GPIO.LOW)
    GPIO.output(var['pin']['step'], GPIO.LOW)
    GPIO.cleanup()
  if what == '4-phase_OK_but_class_version':
    if 1:
      # Raspberry-Pi-A4988-4-Phase.png
      # https://courses.ideate.cmu.edu/16-223/f2021/text/code/pico-stepper.html
      # GPIO-Pin-Nummern
      DIR_PIN = 17
      STEP_PIN = 18
      # Setze den Modus auf GPIO.BOARD
      #GPIO.setmode(GPIO.BOARD)
      GPIO.setmode(GPIO.BCM)
      # Initialisiere die GPIO-Pins
      GPIO.setup(DIR_PIN, GPIO.OUT)
      GPIO.setup(STEP_PIN, GPIO.OUT)
      #--------------------------------------------------------------------------------
    class A4988:
      def __init__(self, DIR=DIR_PIN, STEP=STEP_PIN):
        """Diese Klasse repräsentiert einen A4988-Schrittmotor-Treiber. Es verwendet zwei Ausgangspins
        für die Richtungs- und Schritt-Steuerungssignale."""
        self._dir = DIR
        self._step = STEP
        GPIO.output(self._dir, GPIO.LOW)
        GPIO.output(self._step, GPIO.LOW)
      def step(self, forward=True):
        """Emitiere einen Schrittimpuls, mit optionaler Richtungsangabe."""
        GPIO.output(self._dir, GPIO.HIGH if forward else GPIO.LOW)
        GPIO.output(self._step, GPIO.HIGH)
        # time.sleep(1e-6)
        GPIO.output(self._step, GPIO.LOW)
      def move_sync(self, steps, speed=1000.0):
        """Bewege den Schrittmotor die angegebene Anzahl von Schritten vorwärts oder rückwärts mit der angegebenen Geschwindigkeit in Schritten pro Sekunde. 
        Beachte, dass diese Funktion nicht zurückkehrt, bis die Bewegung abgeschlossen ist, und daher nicht mit asynchronen Ereignisschleifen kompatibel ist.
        """
        forward = steps >= 0
        GPIO.output(self._dir, GPIO.HIGH if forward else GPIO.LOW)
        time_per_step = 1.0 / speed
        for count in range(abs(steps)):
          GPIO.output(self._step, GPIO.HIGH)
          # time.sleep(1e-6)
          GPIO.output(self._step, GPIO.LOW)
          time.sleep(time_per_step)
      def deinit(self):
        """Verwalte die Ressourcenfreigabe als Teil des Objektlebenszyklus."""
        GPIO.cleanup()
        self._dir = None
        self._step = None
      def __enter__(self): return self
      def __exit__(self): self.deinit() # Deinitialisiert die Hardware automatisch beim Verlassen eines Kontexts.
    #--------------------------------------------------------------------------------
    # Beispiel für einen Schrittmotor.
    stepper = A4988()
    print("Start des Schrittmotor-Tests.")
    speed = 200
    stepper.move_sync(200, speed)
    time.sleep(1.0)
    stepper.move_sync(-200, speed)
    time.sleep(1.0)
    '''
    while True:
      print(f"Geschwindigkeit: {speed} Schritte/Sekunde.")
      stepper.move_sync(800, speed)
      time.sleep(1.0)
      stepper.move_sync(-800, speed)
      time.sleep(1.0)
      speed *= 1.2
      if speed > 2000: speed = 100
    '''
if driver == 'OWN_H-BRIDGE': # for an ELEGOO 4 Kanal DC 5V
  var = {
     'pic':['']
    ,'cmd':'python3 02_motor.py OWN_H-BRIDGE 5 230'
    ,'deg':int(what),'repeat':int(sys.argv[3])
    ,'pin':{'left':24,'right':23} # GPIO pin numbers!
    ,'one_Rotation':231 # approximation
    ,'max_rotation':360,'steps':5,'t_wait':0.1 # perfect rotation with 0.1, 0.3, 0.5 + one_Rotation = 231 + repeat = 230 + deg = 5
  }
  if var['deg'] > 0: GPIO_DIR_PIN = 24
  else: GPIO_DIR_PIN = 23; var['deg'] *= -1
  if var['deg'] > var['one_Rotation'] or var['deg'] == 0: sys.exit('Error: 0 < n-Drehung < '+str(var['one_Rotation']))
  GPIO.setmode(GPIO.BCM) # GPIO Nummern statt Board Nummern
  GPIO.setup(GPIO_DIR_PIN, GPIO.OUT) # GPIO Modus zuweisen
  GPIO.output(GPIO_DIR_PIN, GPIO.LOW) # aus
  t_deg = var['deg'] / var['max_rotation']
  for a in range(0,var['repeat']):
    GPIO.output(GPIO_DIR_PIN, GPIO.HIGH) # an
    time.sleep(t_deg)
    GPIO.output(GPIO_DIR_PIN, GPIO.LOW) # an
    time.sleep(var['t_wait'])
  GPIO.cleanup()
if driver == 'L298N': # for an L298N step motor driver
  if what == '2-phase':
    var = {
       'pic':'Raspberry-Pi-L298N-2-Phase.jpg'
      ,'cmd':'python3 02_motor.py L298N 2-phase -1'
      ,'n':int(sys.argv[3])
      ,'pin':{'ena':18,'in1':27,'in2':17} # GPIO pin numbers!
      ,'one_Rotation_at_power_80_in_t':1.038 # approximation
      ,'p':0,'m':1000,'power':80
    }
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(var['pin']['in1'],GPIO.OUT)
    GPIO.setup(var['pin']['in2'],GPIO.OUT)
    GPIO.setup(var['pin']['ena'],GPIO.OUT)
    GPIO.output(var['pin']['in1'],GPIO.LOW)
    GPIO.output(var['pin']['in2'],GPIO.LOW)
    var['p'] = GPIO.PWM( var['pin']['ena'], var['m'] )
    var['p'].start( var['power'] )
    if var['n'] > 0 and var['n'] <= 50:
      GPIO.output(var['pin']['in1'],GPIO.HIGH)
      GPIO.output(var['pin']['in2'],GPIO.LOW)
      #time.sleep( var['one_Rotation_at_power_80_in_t'] / var['n'] )
      time.sleep( 5 )
      GPIO.output(var['pin']['in1'],GPIO.LOW)
      GPIO.output(var['pin']['in2'],GPIO.LOW)
    if var['n'] < 0 and var['n'] >= -50:
      GPIO.output(var['pin']['in1'],GPIO.LOW)
      GPIO.output(var['pin']['in2'],GPIO.HIGH)
      #time.sleep( var['one_Rotation_at_power_80_in_t'] / -var['n'] )
      time.sleep( 5 )
      GPIO.output(var['pin']['in1'],GPIO.LOW)
      GPIO.output(var['pin']['in2'],GPIO.LOW)
    GPIO.cleanup()
  if what == '4-Phase':
    def repeatMe( var ):
      for a in range( 0, len( var['seq'] )):
        if a == var['i']:
          var['arr'] = ['FR^_^EE']
          for c in var['seq'][a]:
            if c == 0: var['arr'].append( GPIO.LOW )
            else: var['arr'].append( GPIO.HIGH )
          GPIO.output(var['pin']['1'],var['arr'][1])
          GPIO.output(var['pin']['2'],var['arr'][2])
          GPIO.output(var['pin']['3'],var['arr'][3])
          GPIO.output(var['pin']['4'],var['arr'][4])
          time.sleep( var['t_sleep'] )
          return
    var = {
       'pic':'Raspberry-Pi-L298N-4-Phase.jpg'
      ,'cmd':'python3 02_motor.py L298N 4-phase -200'
      ,'n':int(sys.argv[3]) 
      ,'pin':{'1':13,'2':11,'3':15,'4':12} # physical pins! not GPIO pin numbers!
      ,'one_Rotation':400
      ,'i':0,'y':0,'pos':0,'neg':0,'t_sleep':0.003,'arr':[]
      ,'seq':[
          [1,0,0,0]
        ,[1,1,0,0]
        ,[0,1,0,0]
        ,[0,1,1,0]
        ,[0,0,1,0]
        ,[0,0,1,1]
        ,[0,0,0,1]
        ,[1,0,0,1] 
      ]
    }
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(var['pin']['1'],GPIO.OUT); GPIO.setup(var['pin']['2'],GPIO.OUT)
    GPIO.setup(var['pin']['3'],GPIO.OUT); GPIO.setup(var['pin']['4'],GPIO.OUT)
    try:
      GPIO.output(var['pin']['1'],GPIO.LOW); GPIO.output(var['pin']['2'],GPIO.LOW)
      GPIO.output(var['pin']['3'],GPIO.LOW); GPIO.output(var['pin']['4'],GPIO.LOW)
      if var['n'] > 0 and var['n'] <=  var['one_Rotation']:
        for y in range( var['n'], 0, -1 ):
          if var['neg'] == 1:
            if var['i'] == 7: var['i'] = 0
            else: var['i'] += 1
            var['y'] += 1
            var['neg'] = 0
          var['pos'] = 1
          repeatMe( var )
          if var['i'] == 7: var['i'] = 0; continue
          var['i'] += 1  
      if var['n'] < 0 and var['n'] >= -var['one_Rotation']:
        var['n'] = -var['n']
        for y in range( var['n'], 0, -1 ):
          if var['pos'] == 1:
            if var['i'] == 0: var['i'] = 7
            else: var['i'] -= 1
            y = y + 3
            var['pos'] = 0
          var['neg'] = 1
          repeatMe( var )
          if var['i'] == 0: var['i'] = 7; continue
          var['i'] -= 1
    except KeyboardInterrupt: GPIO.cleanup()
