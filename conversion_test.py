import math

class Test:
    __dry_air_gas_constant__ = 287.058
    __standard_air_density__ = 1.225;

    def __init__(self):
        print(' 10 = %f' % self.c(  15.81))
        print(' 20 = %f' % self.c(  63.23))
        print(' 30 = %f' % self.c( 142.26))
        print(' 40 = %f' % self.c( 252.90))         
        print(' 50 = %f' % self.c( 395.16))
        print('100 = %f' % self.c(1580.64))
        print('125 = %f' % self.c(2469.75))
        print('150 = %f' % self.c(3556.44))        

    def c(self, x):
        return self.meters_per_second_to_knots(self.indicated_airspeed(x))
    
    def meters_per_second_to_knots(self, x):
        return x * 1.94384
        
    def indicated_airspeed(self, q):
        if q < 0: q = 0
        return math.sqrt(2.0 * q / self.__standard_air_density__)

Test()
