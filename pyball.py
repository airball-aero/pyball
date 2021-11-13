#!/usr/bin/python2

import queue
import threading
import socket
import time
import os
import sys
import pygame
import math

########################################################################

class ProbeReader(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)
        self.__q__ = queue.Queue()
    
    def run(self):
        self.__setup__()
        while True:
            self.__q__.put(self.__infile__.readline().strip())
            
    def __setup__(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(('192.168.4.1', 80))
        self.__infile__ = s.makefile()

    def get(self):
        try:
            return self.__q__.get_nowait()
        except queue.Empty:
            return None

########################################################################

class ProbeData:

    def __init__(self, fields):
        self.__translate__(fields)

    def type(self):
        pass

    def __translate__(self, fields):
        self.seq = int(fields[0])

class ProbeAirData(ProbeData):

    def __init__(self, fields):
        ProbeData.__init__(self, fields)

    def empty():
        return ProbeAirData(['0' for i in range(0, 10)])
        
    def type(self):
        return 'air'

    def __translate__(self, fields):
        ProbeData.__translate__(self, fields)
        self.p = float(fields[1])
        self.t = float(fields[2])
        self.dp0 = float(fields[3])
        self.dpa = float(fields[4])
        self.dpb = float(fields[5])

class ProbeAirReducedData(ProbeData):

    def __init__(self, fields):
        ProbeData.__init__(self, fields)

    def empty():
        return ProbeAirReducedData(['0' for i in range(0, 10)])
        
    def type(self):
        return 'air_reduced'

    def __translate__(self, fields):
        ProbeData.__translate__(self, fields)
        self.alpha = float(fields[1])
        self.beta = float(fields[2])
        self.q = float(fields[3])
        self.p = float(fields[4])
        self.t = float(fields[5])

class ProbeBatteryData(ProbeData):

    def __init__(self, fields):
        ProbeData.__init__(self, fields)

    def type(self):
        return 'battery'

    def __translate__(self, fields):
        # ProbeData.__translate__(self, fields)
        pass # TODO

class ProbeUnknownData(ProbeData):

    def __init__(self, type, fields):
        ProbeData.__init__(fields)
        self.__type__ = type

    def type(self):
        return self.__type__

    def __translate__(self, fields):
        pass
    
def get_probe_data(line):
    fields = line.split(',')
    if fields[0] == '$A':
        return ProbeAirData(fields[1:])
    if fields[0] == '$AR':
        return ProbeAirReducedData(fields[1:])
    if fields[0] == '$B':    
        return ProbeBatteryData(fields[1:])
    return ProbeUnknownData(fields[0], fields[1:])
    
########################################################################
        
class ProbeDataSource:

    def __init__(self):
        self.__probe_reader__ = ProbeReader()
        self.__probe_reader__.start()
        self.__of__ = open('data.csv', 'a')
    
    def get(self):
        line = self.__probe_reader__.get()
        if line == None: return None
        self.__of__.write("%s,%s\n" % (time.time(), line))
        self.__of__.flush()
        return get_probe_data(line)

########################################################################

class Application:

    def __init__(self):
        self.__init_pygame__()
        
    def run(self):
        pass

    def __init_regular__(self):
        pygame.display.init()
        self.__screen__ = pygame.display.set_mode([800, 480])

    def __init_framebuffer__(self):
        drivers = ['fbcon', 'directfb', 'svgalib']
        found = False
        for driver in drivers:
            # Make sure that SDL_VIDEODRIVER is set
            if not os.getenv('SDL_VIDEODRIVER'):
                os.putenv('SDL_VIDEODRIVER', driver)
                try:
                    pygame.display.init()
                    pass
                except pygame.error:
                    print('Driver: {0} failed.'.format(driver))
                    continue
            found = True
            break
        if not found:
            raise Exception('No suitable video driver found!')
        screen_size = (
            pygame.display.Info().current_w,
            pygame.display.Info().current_h,
        )
        self.__screen__ = pygame.display.set_mode(screen_size, pygame.FULLSCREEN)
        
    def __init_pygame__(self):
        self.__init_regular__()
        self.__screen__.fill((0, 0, 0))                
        pygame.font.init()
        pygame.display.update()
        self.__clock__ = pygame.time.Clock()

    def screen(self):
        return self.__screen__

    def clock(self):
        return self.__clock__
    
########################################################################

class DataView(Application):
    
    def __init__(self):
        Application.__init__(self)
        self.probe_data = ProbeDataSource()

    def run(self):
        done = False
        while not done:
            try:
                done = self.__one_cycle__()
            except Exception as e:
                print(e)
                done = True
        pygame.quit()
        os._exit(1) # kill lingering threads

    def __one_cycle__(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return True
            if event.type == pygame.KEYDOWN:
                return True
        while True:
            v = self.probe_data.get()
            if v == None:
                break
            self.handle_data(v)
        self.clock().tick(60)
        pygame.display.flip()
        return False
    
    def handle_data(self, v):
        pass
        
########################################################################

class SimpleDataView(DataView):

    __box_unit__ = 30
    __font_size__ = 30
    __padding__ = 10

    __dry_air_gas_constant__ = 287.058
    __standard_air_density__ = 1.225;
    
    def __init__(self):
        DataView.__init__(self)
        self.__font__ = pygame.font.Font(
            '09391_ContextRepriseCondensedSSiCondensed.ttf',
            self.__font_size__)
        self.__a__ = ProbeAirData.empty()
        self.__ar__ = ProbeAirReducedData.empty()
    
    def handle_data(self, v):
        if v.type() == 'air_reduced':
            self.__ar__ = v
        elif v.type() == 'air':
            self.__a__ = v
        else:
            return
        self.screen().fill((0, 0, 0))
        self.redisplay()
        
    def redisplay(self):
        self.show_data([
            [
                [
                    '$AR q',
                    'Pa',
                    "%05.0f",
                    self.__ar__.q,
                ],
                [
                    '$AR q',
                    '"h2o',
                    "%03.2f",
                    self.pascals_to_in_h2o(self.__ar__.q),
                ],
                [
                    '$AR q',
                    'kias',
                    "%03.0f",
                    self.meters_per_second_to_knots(self.indicated_airspeed(self.__ar__.q)),
                ],
                [
                    'skip',
                ],
                [
                    '$AR alpha',
                    'deg',
                    "%03.1f",
                    self.__ar__.alpha,
                ],
                [
                    '$AR beta',
                    'deg',
                    "%03.1f",
                    self.__ar__.beta,
                ],
                [
                    'skip',
                ],
                [
                    '$AR p',
                    'Pa',
                    "%06.0f",
                    self.__ar__.p,
                ],
                [
                    'skip',
                ],
                [
                    '$AR t',
                    'degC',
                    "%03.1f",
                    self.__ar__.t,
                ],
            ],
            [
                [
                    '$A dp0',
                    'Pa',
                    "%05.0f",
                    self.__a__.dp0
                ],
                [
                    '$A dp0',
                    '"h2o',
                    "%03.2f",
                    self.pascals_to_in_h2o(self.__a__.dp0),
                ],
                [
                    '$A dp0',
                    'kias',
                    "%03.0f",
                    self.meters_per_second_to_knots(self.indicated_airspeed(self.__a__.dp0)),
                ],
                [
                    'skip',
                ],
                [
                    '$A dpa',
                    'Pa', "%05.0f",
                    self.__a__.dpa,
                ],
                [
                    '$A dpb',
                    'Pa', "%05.0f",
                    self.__a__.dpb,
                ],
                [
                    'skip',
                ],
                [
                    '$A p',
                    'Pa',
                    '%06.0f',
                    self.__a__.p,
                ],
                [
                    'skip',
                ],
                [
                    '$A t',
                    'degC',
                    "%03.1f",
                    self.__a__.t,
                ],
            ],
        ])

    def show_data(self, data):
        def show_item(d, col, i):
            if d[0] == 'skip': return
            clr = (i % 2) == 0
            self.text(col * 15 + 0, i, d[0], clr)
            self.text(col * 15 + 5, i, d[2] % d[3], clr)
            self.text(col * 15 + 9, i, d[1], clr)
        
        for i in range(0, len(data[0])):
            show_item(data[0][i], 0, i)
        for i in range(0, len(data[1])):
            show_item(data[1][i], 1, i)
        
    def text(self, x, y, str, clr):
        size = self.__font__.size(str)
        if clr:
            fg = 0xff, 0xc0, 0xc0
        else:
            fg = 0xc0, 0xff, 0xc0
        bg = 0, 0, 0
        ren = self.__font__.render(str, 0, fg, bg)
        self.screen().blit(
            ren, (
                x * self.__box_unit__ + self.__padding__,
                y * self.__box_unit__ + self.__padding__,
            ))

    def float_to_string(self, x):
        return "%0.3f" % x
        
    def pressure_altitude(self, t, p, qnh=101325.0):
        ratio = (qnh / p);
        t_kelvin = t + 273.15;
        power = 1 / 5.257;
        return (pow(ratio, power) - 1.0) * t_kelvin / 0.0065

    def true_airspeed(self, q, p, t):
        return math.sqrt(2.0 * q / self.dry_air_density(p, t))

    def indicated_airspeed(self, q):
        if q < 0: q = 0
        return math.sqrt(2.0 * q / self.__standard_air_density__)
    
    def dry_air_density(self, p, t):
        return p / (self.__dry_air_gas_constant__ * self.celsius_to_kelvin(t))

    def pascals_to_in_h2o(self, x):
        return x * 0.00401865    

    def celsius_to_kelvin(self, x):
        return x + 273.15

    def meters_to_feet(self, x):
        return x * 3.28084

    def meters_per_second_to_knots(self, x):
        return x * 1.94384
    
########################################################################

SimpleDataView().run()
